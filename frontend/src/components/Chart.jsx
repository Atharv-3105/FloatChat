import PlotlyComponent from "react-plotly.js";
import { useMemo } from "react";

const Plot = PlotlyComponent.default || PlotlyComponent;

export default function Chart({ data, selectedFloat }) {
  if (
    !data ||
    !Array.isArray(data.x) ||
    !Array.isArray(data.y) ||
    data.x.length === 0 ||
    data.y.length === 0
  ) {
    return <p>No chart data available to display.</p>;
  }

  // useMemo will prevent re-calculating on every render, only when data changes.
  const { allTrace, highlightTrace } = useMemo(() => {
    const points = data.x.map((xVal, i) => ({
      x: xVal,
      y: data.y[i],
      id: data.ids ? data.ids[i] : null,
    })).sort((a, b) => a.x - b.x); // Sort by x-axis value (e.g., pressure)

    const allTrace = {
      x: points.map(p => p.x),
      y: points.map(p => p.y),
      type: "scatter",
      mode: "lines",
      name: "All Floats",
      line: {
        color: '#36a2eb',
        width: 2,
      }
    };

    const highlightPoints = selectedFloat 
      ? points.filter(p => p.id === selectedFloat)
      : [];

    const highlightTrace = {
      x: highlightPoints.map(p => p.x),
      y: highlightPoints.map(p => p.y),
      type: "scatter",
      mode: "markers",
      name: `Float ${selectedFloat}`,
      marker: {
        color: '#ff4d4d',
        size: 10,
        symbol: 'diamond',
      }
    };

    return { allTrace, highlightTrace };
  }, [data, selectedFloat]);

  return (
    <Plot
      data={[allTrace, highlightTrace]}
      layout={{
        title: data.title || "Chart",
        xaxis: { title: data.x_label || "" },
        yaxis: { title: data.y_label || "" },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0.1)',
        font: {
          color: '#ffffff'
        },
        showlegend: true,
      }}
      style={{ width: "100%", height: "90%" }}
    />
  );
}
