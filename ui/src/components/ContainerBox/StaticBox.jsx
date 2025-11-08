import { useState, useRef, useEffect } from "react";
import "./Box.scss"
 
export default function Box({ label, x, y }) {
  return (
    <div
      className="box-container"
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: 120,
        height: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {label}
    </div>
  );
}
