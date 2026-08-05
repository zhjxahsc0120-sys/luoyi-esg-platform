import * as Cesium from "cesium";
export class LayerRegistry {
  private readonly layers = new Map<string, Cesium.Entity[]>();
  set(id: string, entities: Cesium.Entity[]) {
    this.layers.set(id, entities);
  }
  get(id: string) {
    return this.layers.get(id) || [];
  }
  all() {
    return [...this.layers.values()].flat();
  }
  show(id: string, visible: boolean) {
    this.get(id).forEach((e) => (e.show = visible));
  }
  remove(id: string, viewer: Cesium.Viewer) {
    this.get(id).forEach((e) => viewer.entities.remove(e));
    this.layers.delete(id);
  }
  clear(viewer: Cesium.Viewer) {
    this.layers.forEach((items) =>
      items.forEach((e) => viewer.entities.remove(e)),
    );
    this.layers.clear();
  }
}
