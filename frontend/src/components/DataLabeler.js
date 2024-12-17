// src/components/DataLabeler.js

import React, { useEffect, useState, useMemo, useRef } from 'react';
import Plot from 'react-plotly.js';
import { useTable, useRowSelect, useSortBy } from 'react-table';
import { fetchUnlabeledData, batchLabel } from '../api';
import './DataLabeler.css'; // Optional: Für zusätzliche Stile

// Checkbox-Komponente für react-table
const IndeterminateCheckbox = React.forwardRef(
  ({ indeterminate, ...rest }, ref) => {
    const defaultRef = React.useRef();
    const resolvedRef = ref || defaultRef;

    React.useEffect(() => {
      if (resolvedRef.current) {
        resolvedRef.current.indeterminate = indeterminate;
      }
    }, [resolvedRef, indeterminate]);

    return (
      <input type="checkbox" ref={resolvedRef} {...rest} />
    );
  }
);

function DataLabeler() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState(1000); // Standardmäßig 1000 Datenpunkte
  const lastSelectedRow = useRef(null); // Ref für die letzte ausgewählte Zeile

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const unlabeled = await fetchUnlabeledData(limit);
      setData(unlabeled);
      setLoading(false);
    }
    loadData();
  }, [limit]); // Neuladen der Daten, wenn 'limit' sich ändert

  const columns = useMemo(
    () => [
      {
        Header: 'Select',
        accessor: 'select',
        disableSortBy: true, // Deaktiviert das Sortieren für die Auswahl-Spalte
        Cell: ({ row }) => (
          <div>
            <IndeterminateCheckbox {...row.getToggleRowSelectedProps()} />
          </div>
        ),
      },
      { Header: 'ID', accessor: 'id' },
      { Header: 'Timestamp', accessor: 'timestamp' },
      { Header: 'ax', accessor: 'ax' },
      { Header: 'ay', accessor: 'ay' },
      { Header: 'az', accessor: 'az' },
      { Header: 'gx', accessor: 'gx' },
      { Header: 'gy', accessor: 'gy' },
      { Header: 'gz', accessor: 'gz' },
      { Header: 'Pulse', accessor: 'pulse' },
    ],
    []
  );

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
    selectedFlatRows,
    state: { selectedRowIds },
    toggleAllRowsSelected,
    toggleRowSelected,
  } = useTable(
    {
      columns,
      data,
      getRowId: row => row.id,
      initialState: {
        sortBy: [{ id: 'id', desc: false }],
      },
      autoResetSelectedRows: false,
    },
    useSortBy,
    useRowSelect,
    hooks => {
      hooks.visibleColumns.push(columns => [
        columns[0],
        ...columns.slice(1),
      ]);
    }
  );

  const handleLabel = async (labelValue) => {
    const selected = selectedFlatRows.map(row => row.original.id);
    const allIds = data.map(d => d.id);
    const unselected = allIds.filter(id => !selected.includes(id));

    try {
      if (selected.length > 0) {
        await batchLabel(selected, labelValue);
        console.log(`Gelabelt ${selected.length} ausgewählte Datenpunkte mit Label ${labelValue}.`);
      }

      if (unselected.length > 0) {
        const oppositeLabel = labelValue === 1 ? 0 : 1;
        await batchLabel(unselected, oppositeLabel);
        console.log(`Gelabelt ${unselected.length} nicht ausgewählte Datenpunkte mit Label ${oppositeLabel}.`);
      }

      alert("Daten erfolgreich gelabelt.");
      const updatedData = await fetchUnlabeledData(limit);
      setData(updatedData);
      toggleAllRowsSelected(false);
    } catch (error) {
      console.error("Fehler beim Labeln der Daten:", error);
      alert("Fehler beim Labeln der Daten.");
    }
  };

  const handleSelectAll = () => {
    toggleAllRowsSelected(true);
  };

  const handleDeselectAll = () => {
    toggleAllRowsSelected(false);
  };

  const handleRowClick = (row, event) => {
    if (event.shiftKey && lastSelectedRow.current !== null) {
      const currentIndex = rows.findIndex(r => r.id === row.id);
      const lastIndex = rows.findIndex(r => r.id === lastSelectedRow.current.id);
      const [start, end] = [lastIndex, currentIndex].sort((a, b) => a - b);
      const idsToSelect = rows.slice(start, end + 1).map(r => r.original.id);
      idsToSelect.forEach(id => toggleRowSelected(id, true));
    } else {
      toggleRowSelected(row.original.id, !selectedRowIds[row.id]);
      lastSelectedRow.current = row;
    }
  };

  const handlePlotSelect = (event) => {
    console.log('Plot Selection Event:', event);
    if (event && event.points) {
      const selectedIds = Array.from(new Set(event.points.map(point => point.x)));
      console.log('Selected IDs from Plot:', selectedIds);
      toggleAllRowsSelected(false);
      selectedIds.forEach(id => toggleRowSelected(id, true));
    }
  };

  if (loading) {
    return <div>Lade Daten...</div>;
  }

  const interval = 20;
  const tickVals = data
    .filter((d, index) => (d.id % interval === 0) || d.id === data[data.length - 1].id)
    .map(d => d.id);

  const tickText = data
    .filter((d, index) => (d.id % interval === 0) || d.id === data[data.length - 1].id)
    .map(d => d.timestamp);

  // Daten für Plotly vorbereiten
  const plotData = [
    {
      x: data.map(d => d.id),
      y: data.map(d => d.ax),
      type: 'scatter',
      mode: 'lines',
      name: 'ax',
      line: { color: 'red' },
      hovertemplate: `ID: %{x}<br>Timestamp: %{text}<br>ax: %{y}<extra></extra>`,
      text: data.map(d => d.timestamp),
    },
    {
      x: data.map(d => d.id),
      y: data.map(d => d.ay),
      type: 'scatter',
      mode: 'lines',
      name: 'ay',
      line: { color: 'blue' },
      hovertemplate: `ID: %{x}<br>Timestamp: %{text}<br>ay: %{y}<extra></extra>`,
      text: data.map(d => d.timestamp),
    },
    {
      x: data.map(d => d.id),
      y: data.map(d => d.az),
      type: 'scatter',
      mode: 'lines',
      name: 'az',
      line: { color: 'green' },
      hovertemplate: `ID: %{x}<br>Timestamp: %{text}<br>az: %{y}<extra></extra>`,
      text: data.map(d => d.timestamp),
    },
    {
      x: data.map(d => d.id),
      y: data.map(d => d.gx),
      type: 'scatter',
      mode: 'lines',
      name: 'gx',
      line: { color: 'orange' },
      hovertemplate: `ID: %{x}<br>Timestamp: %{text}<br>gx: %{y}<extra></extra>`,
      text: data.map(d => d.timestamp),
    },
    {
      x: data.map(d => d.id),
      y: data.map(d => d.gy),
      type: 'scatter',
      mode: 'lines',
      name: 'gy',
      line: { color: 'purple' },
      hovertemplate: `ID: %{x}<br>Timestamp: %{text}<br>gy: %{y}<extra></extra>`,
      text: data.map(d => d.timestamp),
    },
    {
      x: data.map(d => d.id),
      y: data.map(d => d.gz),
      type: 'scatter',
      mode: 'lines',
      name: 'gz',
      line: { color: 'brown' },
      hovertemplate: `ID: %{x}<br>Timestamp: %{text}<br>gz: %{y}<extra></extra>`,
      text: data.map(d => d.timestamp),
    },
    {
      x: data.map(d => d.id),
      y: data.map(d => d.pulse),
      type: 'scatter',
      mode: 'lines',
      name: 'pulse',
      line: { color: 'black' },
      yaxis: 'y2', // Pulse auf einer zweiten Y-Achse
      hovertemplate: `ID: %{x}<br>Timestamp: %{text}<br>Pulse: %{y}<extra></extra>`,
      text: data.map(d => d.timestamp),
    }
  ];

  const layout = {
    title: `Letzte ${limit} Sensordaten`,
    dragmode: 'select', // Ermöglicht Box- oder Lasso-Auswahl
    selectdirection: 'h', // Horizontale Auswahl
    xaxis: {
      title: 'ID Nummer',
      type: 'linear',
      tickvals: tickVals,
      ticktext: tickText,
      tickangle: -45,
      tickfont: { size: 10 },
      ticks: 'inside',
      ticklen: 5,
      tickwidth: 1,
      showgrid: false,
    },
    yaxis: {
      title: 'Sensorwerte',
      showgrid: true,
    },
    yaxis2: {
      title: 'Pulse',
      overlaying: 'y',
      side: 'right',
      showgrid: false,
      zeroline: false,
    },
    margin: { l: 50, r: 50, t: 50, b: 150 },
  };

  return (
    <div>
      <h2>Daten Labeln</h2>

      {/* Steuerung zur Einstellung der Anzahl der Datenpunkte */}
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="limit-select" style={{ marginRight: '10px' }}>
          Anzahl der anzuzeigenden Datenpunkte:
        </label>
        <select
          id="limit-select"
          value={limit}
          onChange={(e) => setLimit(parseInt(e.target.value))}
        >
          <option value={200}>200</option>
          <option value={500}>500</option>
          <option value={1000}>1000</option>
          <option value={2000}>2000</option>
        </select>
      </div>

      <Plot
        data={plotData}
        layout={layout}
        useResizeHandler
        style={{ width: "100%", height: "600px" }}
        onSelected={handlePlotSelect} // Event-Handler für Auswahl im Plot
      />
      <h3>Tabelle der Sensordaten</h3>
      {/* "Select All" und "Deselect All" Buttons */}
      <div style={{ marginBottom: '10px' }}>
        <button onClick={handleSelectAll} style={{ marginRight: '10px' }}>
          Alle auswählen
        </button>
        <button onClick={handleDeselectAll}>
          Auswahl aufheben
        </button>
      </div>
      <table {...getTableProps()} className="sensor-table">
        <thead>
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()} key={headerGroup.id}>
              {headerGroup.headers.map(column => (
                <th
                  {...column.getHeaderProps(column.getSortByToggleProps())} // Hinzufügen der Sortier-Props
                  key={column.id}
                  className="sensor-table-header"
                >
                  {column.render('Header')}
                  {/* Sortierindikatoren */}
                  <span>
                    {column.isSorted
                      ? column.isSortedDesc
                        ? ' 🔽'
                        : ' 🔼'
                      : ''}
                  </span>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {rows.map(row => {
            prepareRow(row);
            return (
              <tr
                {...row.getRowProps()}
                key={row.id}
                onClick={(e) => handleRowClick(row, e)}
                style={{ cursor: 'pointer' }}
              >
                {row.cells.map(cell => (
                  <td
                    {...cell.getCellProps()}
                    key={cell.column.id}
                    className="sensor-table-cell"
                  >
                    {cell.render('Cell')}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div style={{ marginTop: '20px' }}>
        <button onClick={() => handleLabel(1)} style={{ marginRight: '10px' }}>
          Label ausgewählt als Trinkvorgang
        </button>
        <button onClick={() => handleLabel(0)}>
          Label ausgewählt als Kein Trinkvorgang
        </button>
      </div>
    </div>
  );
}

export default DataLabeler;
