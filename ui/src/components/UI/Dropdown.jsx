import { useState, useRef, useEffect } from "react";
import "./UI.scss";

export default function Dropdown({
  options = [],
  value = null,
  placeholder = "MODE",
  onChange = () => {},
  className = "",
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef();

  const handleSelect = (option) => {
    setOpen(false);
    onChange(option);
  };

  // Handle clicking outside
  const handleBlur = (e) => {
    if (!ref.current.contains(e.relatedTarget)) setOpen(false);
  };

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div
      className={`dropdown ${className}`}
      tabIndex={0}
      onBlur={handleBlur}
      ref={ref}
    >
      <button
        className="dropdown-trigger"
        onClick={() => setOpen((show) => !show)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className={value ? "dropdown-value" : "dropdown-placeholder"}>
          {value ? value.label : placeholder}
        </span>
        <svg
          className={`dropdown-arrow ${open ? "dropdown-arrow-open" : ""}`}
          viewBox="0 0 16 16"
          width={20}
          height={20}
        >
          <path
            d="M4 6l4 4 4-4"
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      <ul
        className={`dropdown-list${open ? " dropdown-list-open" : ""}`}
        tabIndex={-1}
        role="listbox"
      >
        {options.map((option) => (
          <li
            key={option.value}
            tabIndex={0}
            className={`dropdown-option${
              value && value.value === option.value
                ? " dropdown-option-selected"
                : ""
            }`}
            onClick={() => handleSelect(option)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSelect(option);
            }}
            role="option"
            aria-selected={value && value.value === option.value}
          >
            {option.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
