import React from "react";
import "./ObserverPiece.css";

function ObserverPiece({ observer, isSelected, onClick }) {
  return (
    <div
      className={`observer-piece-container ${isSelected ? "selected" : ""}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
    >
      {/* Observer icon */}
      <div className="observer-piece">
        <span className="observer-symbol">👁️</span>
        <span className="observer-badge">OBS</span>
      </div>

      {/* Observation aura visualization (shown when selected) */}
      {isSelected && (
        <div className="observation-aura">
          <div className="aura-ring pulse-animation" />
          <div className="aura-ring pulse-animation delay-1" />
        </div>
      )}

      {/* Stats tooltip */}
      {observer.observations_made !== undefined && (
        <div className="observer-tooltip">
          <div className="tooltip-line">
            <span>Observations:</span>
            <span className="value">{observer.observations_made || 0}</span>
          </div>
          <div className="tooltip-line">
            <span>Range:</span>
            <span className="value">{observer.observation_range || 1} sq</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default ObserverPiece;
