import { configureStore } from "@reduxjs/toolkit";
import { containersApi } from "@/api/containersApi";
import { getContainerMetricsQuery } from "@/api/containerMetrics";

import exampleReducer from "./slices/exampleSlice";
import configReducer from "./slices/configSlice";
import containersReducer from "./slices/containersSlice";
import containerMetricsReducer from "./slices/metricsSlice";

import containerReducer from "./slices/containerSlice";
import tabReducer from "./slices/tabSlice";

export const store = configureStore({
  reducer: {
    [containersApi.reducerPath]: containersApi.reducer,
    [getContainerMetricsQuery.reducerPath]: getContainerMetricsQuery.reducer,
    example: exampleReducer,
    config: configReducer,
    containers: containersReducer,
    containerMetrics: containerMetricsReducer,
    container: containerReducer,
    tab: tabReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(containersApi.middleware)
      .concat(getContainerMetricsQuery.middleware),
});
