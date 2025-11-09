import { configureStore } from "@reduxjs/toolkit";
import { containersApi } from "@/api/containersApi";

import exampleReducer from "./slices/exampleSlice";
import configReducer from "./slices/configSlice";
import containersReducer from "./slices/containersSlice";
import containerReducer from "./slices/containerSlice";
import tabReducer from "./slices/tabSlice";

export const store = configureStore({
  reducer: {
    [containersApi.reducerPath]: containersApi.reducer, // ADD THIS
    example: exampleReducer,
    config: configReducer,
    containers: containersReducer,
    container: containerReducer,
    tab: tabReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(containersApi.middleware),
});
