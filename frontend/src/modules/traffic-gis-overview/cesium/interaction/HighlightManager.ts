import * as Cesium from "cesium";
export class HighlightManager {
  private selected?: Cesium.Entity;
  private backup?: {
    pointSize?: number;
    billboardScale?: number;
  };

  select(entity?: Cesium.Entity) {
    this.restore();
    this.selected = entity;
    if (!entity) return;
    this.backup = {};
    if (entity.point) {
      const sizeProp = entity.point.pixelSize;
      this.backup.pointSize =
        typeof sizeProp?.getValue === "function"
          ? Number(sizeProp.getValue(Cesium.JulianDate.now()) ?? 12)
          : 12;
      entity.point.pixelSize = new Cesium.ConstantProperty(20);
      entity.point.outlineColor = new Cesium.ConstantProperty(Cesium.Color.CYAN);
    }
    if (entity.billboard) {
      const scaleProp = entity.billboard.scale;
      this.backup.billboardScale =
        typeof scaleProp?.getValue === "function"
          ? Number(scaleProp.getValue(Cesium.JulianDate.now()) ?? 1)
          : 1;
      entity.billboard.scale = new Cesium.ConstantProperty(
        Math.max(this.backup.billboardScale * 1.4, 1.35),
      );
    }
  }

  restore() {
    if (this.selected?.point && this.backup?.pointSize != null) {
      this.selected.point.pixelSize = new Cesium.ConstantProperty(this.backup.pointSize);
    }
    if (this.selected?.billboard && this.backup?.billboardScale != null) {
      this.selected.billboard.scale = new Cesium.ConstantProperty(
        this.backup.billboardScale,
      );
    }
    this.selected = undefined;
    this.backup = undefined;
  }
}
