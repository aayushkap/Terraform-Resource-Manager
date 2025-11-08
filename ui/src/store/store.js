import { configureStore } from "@reduxjs/toolkit";
import exampleReducer from "./slices/exampleSlice";
import configReducer from "./slices/configSlice";
import containersReducer from "./slices/containersSlice";

export const store = configureStore({
  reducer: {
    example: exampleReducer,
    config: configReducer,
    containers: containersReducer,
    // Add more slices here as you build them
  },
});
