import * as Cesium from "cesium";

type ParsedBatch = {
  color: string;
  width: number;
  positions: Float64Array;
  indices: Uint32Array;
  lineCount: number;
};

type WorkerSuccess = {
  type: "success";
  batches: ParsedBatch[];
  placemarkCount: number;
};

type WorkerFailure = {
  type: "error";
  message: string;
};

type WorkerResult = WorkerSuccess | WorkerFailure;

type PrimitiveEntry = {
  id: string;
  primitive: Cesium.Primitive;
  originalColor: Cesium.Color;
};

/**
 * SPX KML 含九万余条 LineString。原生 KmlDataSource 会展开成大量 Entity，
 * 因此本层在 Worker 中解析，并按 KML 原始样式批量生成 WebGL 线段。
 * 坐标和每条折线的连接关系不变，只减少 Cesium 对象数量。
 */
export class SpxPrimitiveLayer {
  private readonly entries: PrimitiveEntry[] = [];
  private loadPromise?: Promise<void>;
  private boundingSphere?: Cesium.BoundingSphere;
  private desiredVisible = false;
  private opacity = 1;
  private loaded = false;

  constructor(
    private readonly viewer: Cesium.Viewer,
    private readonly url: string,
  ) {}

  isLoaded() {
    return this.loaded;
  }

  async setVisible(visible: boolean, opacity = this.opacity) {
    this.desiredVisible = visible;
    this.opacity = opacity;
    if (!visible) {
      this.entries.forEach((entry) => {
        entry.primitive.show = false;
      });
      this.viewer.scene.requestRender();
      return;
    }
    await this.ensureLoaded();
    this.entries.forEach((entry) => {
      entry.primitive.show = this.desiredVisible;
    });
    this.setOpacity(opacity);
    this.viewer.scene.requestRender();
  }

  setOpacity(opacity: number) {
    this.opacity = Math.max(0, Math.min(1, opacity));
    for (const entry of this.entries) {
      if (!entry.primitive.ready) continue;
      const attributes = entry.primitive.getGeometryInstanceAttributes(entry.id);
      if (!attributes) continue;
      const color = entry.originalColor.withAlpha(
        entry.originalColor.alpha * this.opacity,
      );
      attributes.color = Cesium.ColorGeometryInstanceAttribute.toValue(color);
    }
    this.viewer.scene.requestRender();
  }

  async locate() {
    if (!this.boundingSphere) {
      throw new Error("请先开启并加载边坡 SPX 图层");
    }
    await this.viewer.camera.flyToBoundingSphere(this.boundingSphere, {
      duration: 0.8,
    });
  }

  destroy() {
    for (const entry of this.entries) {
      this.viewer.scene.primitives.remove(entry.primitive);
    }
    this.entries.length = 0;
    this.boundingSphere = undefined;
    this.loaded = false;
  }

  private ensureLoaded() {
    if (this.loaded) return Promise.resolve();
    if (this.loadPromise) return this.loadPromise;
    this.loadPromise = this.parseInWorker()
      .then((result) => {
        if (!result.batches.length) {
          throw new Error("SPX KML 中没有可渲染的线要素");
        }
        result.batches.forEach((batch, index) =>
          this.addBatch(batch, index),
        );
        this.loaded = true;
      })
      .finally(() => {
        this.loadPromise = undefined;
      });
    return this.loadPromise;
  }

  private parseInWorker(): Promise<WorkerSuccess> {
    return new Promise((resolve, reject) => {
      const worker = new Worker(
        new URL("./spx-kml.worker.ts", import.meta.url),
        { type: "module" },
      );
      worker.onmessage = (event: MessageEvent<WorkerResult>) => {
        worker.terminate();
        if (event.data.type === "error") {
          reject(new Error(event.data.message));
          return;
        }
        resolve(event.data);
      };
      worker.onerror = (event) => {
        worker.terminate();
        reject(new Error(event.message || "SPX 后台解析线程异常"));
      };
      worker.postMessage({ type: "parse", url: this.url });
    });
  }

  private addBatch(batch: ParsedBatch, index: number) {
    const cartesianValues = new Float64Array(batch.positions.length);
    const scratch = new Cesium.Cartesian3();
    for (let offset = 0; offset < batch.positions.length; offset += 3) {
      Cesium.Cartesian3.fromDegrees(
        batch.positions[offset],
        batch.positions[offset + 1],
        batch.positions[offset + 2],
        Cesium.Ellipsoid.WGS84,
        scratch,
      );
      cartesianValues[offset] = scratch.x;
      cartesianValues[offset + 1] = scratch.y;
      cartesianValues[offset + 2] = scratch.z;
    }

    const sphere = Cesium.BoundingSphere.fromVertices(cartesianValues);
    this.boundingSphere = this.boundingSphere
      ? Cesium.BoundingSphere.union(this.boundingSphere, sphere)
      : sphere;
    const color = this.colorFromKml(batch.color);
    const id = `spx-style-${index}`;
    const attributes = new Cesium.GeometryAttributes();
    attributes.position = new Cesium.GeometryAttribute({
      componentDatatype: Cesium.ComponentDatatype.DOUBLE,
      componentsPerAttribute: 3,
      values: cartesianValues,
    });
    const geometry = new Cesium.Geometry({
      attributes,
      indices: batch.indices,
      primitiveType: Cesium.PrimitiveType.LINES,
      boundingSphere: sphere,
    });
    const instance = new Cesium.GeometryInstance({
      id,
      geometry,
      attributes: {
        color: Cesium.ColorGeometryInstanceAttribute.fromColor(color),
      },
    });
    const primitive = this.viewer.scene.primitives.add(
      new Cesium.Primitive({
        geometryInstances: instance,
        appearance: new Cesium.PerInstanceColorAppearance({
          flat: true,
          translucent: color.alpha < 1,
          renderState: {
            depthTest: { enabled: true },
            // Windows/ANGLE 常见上限为 1；超出会让 Cesium 停止整个场景渲染。
            lineWidth: 1,
          },
        }),
        // 自定义批量 Geometry 没有 Cesium 内置 workerName，需同步提交 GPU。
        // 数据解析和坐标整理已在独立 Worker/一次性批处理中完成。
        asynchronous: false,
        releaseGeometryInstances: false,
        show: this.desiredVisible,
      }),
    );
    this.entries.push({ id, primitive, originalColor: color });
  }

  private colorFromKml(value: string) {
    const normalized = value.padStart(8, "f").slice(-8);
    const alpha = Number.parseInt(normalized.slice(0, 2), 16) / 255;
    const blue = Number.parseInt(normalized.slice(2, 4), 16) / 255;
    const green = Number.parseInt(normalized.slice(4, 6), 16) / 255;
    const red = Number.parseInt(normalized.slice(6, 8), 16) / 255;
    return new Cesium.Color(red, green, blue, alpha);
  }
}
