import React from "react";
import PropTypes from "prop-types";
import "./UI.scss";

export default function Button({
  label,
  onClick,
  icon: Icon,
  variant = "default",
  size = "md",
  disabled = false,
  className = "",
  ...props
}) {
  return (
    <button
      className={`btn btn-${variant} btn-${size} ${className}`}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {Icon && <Icon className="btn-icon" />}
      <span className="btn-label">{label}</span>
    </button>
  );
}

Button.propTypes = {
  label: PropTypes.string.isRequired,
  onClick: PropTypes.func,
  icon: PropTypes.elementType,
  variant: PropTypes.oneOf(["default", "primary", "secondary", "subtle"]),
  size: PropTypes.oneOf(["sm", "md", "lg"]),
  disabled: PropTypes.bool,
  className: PropTypes.string,
};
