import { createSlice } from "@reduxjs/toolkit";

const initialState = [];
const containerSlice = createSlice({
  name: "containerMetrics",
  initialState,
  reducers: {
    setContainerMetrics: (state, action) => {
      const container = action.payload;
      const index = state.findIndex((c) => c.id === container.id);

      if (index === -1) {
        // Append
        state.push(container);
      } else {
        // Replace
        state[index] = { ...state[index], ...container };
      }
    },
  },
});

export const { setContainerMetrics } = containerSlice.actions;

export default containerSlice.reducer;
