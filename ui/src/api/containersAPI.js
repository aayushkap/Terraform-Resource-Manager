// src/api/containersApi.js
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const CANVAS_WIDTH = 4000;
const CANVAS_HEIGHT = 3000;
const CENTER_X = CANVAS_WIDTH / 2;
const CENTER_Y = CANVAS_HEIGHT / 2;

export const containersApi = createApi({
  reducerPath: "containersApi",
  baseQuery: fetchBaseQuery({ baseUrl: "http://localhost:8081" }),
  tagTypes: ["Containers"],
  endpoints: (builder) => ({
    getContainers: builder.query({
      query: () => "/containers",
      providesTags: ["Containers"],
      transformResponse: (response) => {
        return response.map((container, index) => {
          const startX = CENTER_X + 200;
          const baseY = CENTER_Y - 200;
          const spacing = 150;

          return {
            id: container.id,
            name: container.info.name,
            label: container.info.name,
            status: container.info.status,
            cpu: container.info.cpu,
            mem: container.info.memory,
            memory: container.info.memory,
            logs: container.info.logs || "",
            timestamp: container.info.timestamp,
            history: container.history || [],
            // default positions which will be overridden for existing containers
            x: startX,
            y: baseY + index * spacing,
          };
        });
      },
      async onQueryStarted(arg, { dispatch, queryFulfilled, getState }) {
        try {
          const { data } = await queryFulfilled;
          const { setContainer } = await import(
            "@/store/slices/containersSlice"
          );

          // Get current containers from state
          const currentContainers = getState().containers;

          data.forEach((newContainer) => {
            const existing = currentContainers.find(
              (c) => c.id === newContainer.id
            );

            if (existing) {
              dispatch(
                setContainer({
                  ...newContainer,
                  x: existing.x,
                  y: existing.y,
                })
              );
            } else {
              dispatch(setContainer(newContainer));
            }
          });
        } catch (err) {
          console.error("Failed to sync containers:", err);
        }
      },
    }),
  }),
});

export const { useGetContainersQuery } = containersApi;
