import * as Cesium from "cesium";
export class HighlightManager {
  private selected?: Cesium.Entity;
  private originalPixelSize?: Cesium.Property;
  private originalOutlineColor?: Cesium.Property;
  select(entity?: Cesium.Entity) {
    this.restore();
    this.selected = entity;
    if (entity?.point) {
      this.originalPixelSize = entity.point.pixelSize;
      this.originalOutlineColor = entity.point.outlineColor;
      entity.point.pixelSize = new Cesium.ConstantProperty(20);
      entity.point.outlineColor = new Cesium.ConstantProperty(
        Cesium.Color.CYAN,
      );
    }
  }
  restore() {
    if (this.selected?.point) {
      if (this.originalPixelSize)
        this.selected.point.pixelSize = this.originalPixelSize;
      if (this.originalOutlineColor)
        this.selected.point.outlineColor = this.originalOutlineColor;
    }
    this.selected = undefined;
    this.originalPixelSize = undefined;
    this.originalOutlineColor = undefined;
  }
}
