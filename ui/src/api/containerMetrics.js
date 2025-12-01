// src/api/containerMetricsApi.js
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const getContainerMetricsQuery = createApi({
  reducerPath: "containerMetricsApi",
  baseQuery: fetchBaseQuery({ baseUrl: "http://localhost:8081" }),
  tagTypes: ["ContainerMetrics"],
  endpoints: (builder) => ({
    getMetrics: builder.query({
      query: () => "/metrics/global",
      providesTags: ["Containers"],
      transformResponse: (response) => {
        return response ?? [];
      },
      async onQueryStarted(arg, { dispatch, queryFulfilled, getState }) {
        try {
          const { data } = await queryFulfilled;
          console.log("data", data);
          const { setContainerMetrics } = await import(
            "@/store/slices/metricsSlice"
          );

          dispatch(setContainerMetrics(data));
        } catch (err) {
          console.error("Failed to sync container metrics:", err);
        }
      },
    }),
  }),
});

export const { useGetMetricsQuery } = getContainerMetricsQuery;
