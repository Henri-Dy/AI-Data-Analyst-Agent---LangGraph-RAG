import Plotly from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
import type { ChartSpec } from "../types";

const Plot = createPlotlyComponent(Plotly);

export function ChartView({ chart }: { chart: ChartSpec }) {
  return (
    <Plot
      data={chart.figure.data as Plotly.Data[]}
      layout={{
        ...(chart.figure.layout as Partial<Plotly.Layout>),
        autosize: true,
        margin: { t: 24, r: 16, b: 40, l: 48 },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "320px" }}
      useResizeHandler
    />
  );
}
