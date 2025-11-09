import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  cpu: { min: 30, max: 70 },
  mem: { min: 30, max: 70 },
  rpm: { min: 30, max: 70 },
  mode: { label: "Manual", value: "manual" },
};

const configSlice = createSlice({
  name: "config",
  initialState,
  reducers: {
    setConfig: (state, action) => {
      console.log(action.payload);
      return { ...state, ...action.payload };
    },
  },
});

// Export actions
export const { setConfig } = configSlice.actions;

// Export reducer
export default configSlice.reducer;
