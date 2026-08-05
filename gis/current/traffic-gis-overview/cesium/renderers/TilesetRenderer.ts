import * as Cesium from "cesium";
export class TilesetRenderer {
  async load(viewer: Cesium.Viewer, url: string) {
    const tileset = await Cesium.Cesium3DTileset.fromUrl(url);
    viewer.scene.primitives.add(tileset);
    return tileset;
  }
  unload(viewer: Cesium.Viewer, tileset: Cesium.Cesium3DTileset) {
    viewer.scene.primitives.remove(tileset);
  }
}
