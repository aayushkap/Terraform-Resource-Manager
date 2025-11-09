import { createSlice } from "@reduxjs/toolkit";

const initialState = [];
const containerSlice = createSlice({
  name: "containers",
  initialState,
  reducers: {
    setContainer: (state, action) => {
      const container = action.payload;
      console.log("setting", container);
      const index = state.findIndex((c) => c.id === container.id);

      if (index === -1) {
        // Append
        state.push(container);
      } else {
        // Replace
        state[index] = { ...state[index], ...container };
      }
    },
    removeContainer: (state, action) => {
      const id = action.payload;
      return state.filter((c) => c.id !== id);
    },
  },
});

export const { setContainer, removeContainer } = containerSlice.actions;

export default containerSlice.reducer;
