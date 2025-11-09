import { createSlice } from "@reduxjs/toolkit";

const initialState = "observability";

const tabSlice = createSlice({
  name: "tab",
  initialState,
  reducers: {
    setTab: (state, action) => {
      return action.payload; // required to return not mutate
    },
  },
});

export const { setTab } = tabSlice.actions;

export default tabSlice.reducer;
