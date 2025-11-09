import { createSlice } from "@reduxjs/toolkit";

const initialState = null;

const containerSlice = createSlice({
  name: "container",
  initialState,
  reducers: {
    setSelectedContainer: (state, action) => {
      return action.payload; // required to return not mutate
    },
  },
});

export const { setSelectedContainer } = containerSlice.actions;

export default containerSlice.reducer;
