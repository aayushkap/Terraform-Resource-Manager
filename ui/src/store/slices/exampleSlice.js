import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  count: 1,
  user: null,
  isLoading: false,
};

const exampleSlice = createSlice({
  name: "example",
  initialState,
  reducers: {
    increment: (state) => {
      state.count += 1;
    },
    decrement: (state) => {
      state.count -= 1;
    },
    setUser: (state, action) => {
      state.user = action.payload;
    },
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
  },
});

// Export actions
export const { increment, decrement, setUser, setLoading } =
  exampleSlice.actions;

// Export reducer
export default exampleSlice.reducer;
