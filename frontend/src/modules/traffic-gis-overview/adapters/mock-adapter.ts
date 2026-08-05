import { layerDefinitions } from "../config/layers.config";
import { mockFeatures } from "../mock/features";
import type {
  TrafficDataAdapter,
  TrafficLayerDefinition,
  TrafficMapContext,
  TrafficMapFeature,
} from "../types";
export class MockTrafficAdapter implements TrafficDataAdapter {
  async getLayers(context: TrafficMapContext) {
    return layerDefinitions.filter(
      (l) => !context.visibleLayerIds || context.visibleLayerIds.includes(l.id),
    );
  }
  async getFeatures(layer: TrafficLayerDefinition, context: TrafficMapContext) {
    return mockFeatures.filter(
      (f) =>
        f.layerId === layer.id &&
        (!context.sectionId || f.properties.sectionId === context.sectionId),
    );
  }
  async getFeatureDetail(feature: TrafficMapFeature) {
    return feature.properties;
  }
}
