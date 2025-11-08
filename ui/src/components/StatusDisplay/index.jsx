import React from "react";
import PropTypes from "prop-types";
import "./StatusDisplay.scss";

export default function StatusDisplay({
  label,
  onClick,
  icon: Icon,
  variant = "default",
  size = "md",
  status = "na",
  className = "",
  ...props
}) {
  return (
    <div
      className={`status-display status-display-${status} status-display-${size} ${className}`}
      onClick={onClick}
      {...props}
    >
      {Icon && <Icon className="status-display-icon" />}
      <span className="status-display-label">{label}</span>
    </div>
  );
}

StatusDisplay.propTypes = {
  label: PropTypes.string.isRequired,
  onClick: PropTypes.func,
  icon: PropTypes.elementType,
  variant: PropTypes.oneOf(["default", "primary", "secondary", "subtle"]),
  size: PropTypes.oneOf(["sm", "md", "lg"]),
  disabled: PropTypes.bool,
  className: PropTypes.string,
};
