import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";

export default function Map({ points, selectedFloat, onSelectFloat }) {
  if (!Array.isArray(points) || points.length === 0) {
    return <p>No map data available to display.</p>;
  }

  // Calculate the center of the map based on the points
  const latitudes = points.map(p => p.latitude);
  const longitudes = points.map(p => p.longitude);
  const centerLat = (Math.min(...latitudes) + Math.max(...latitudes)) / 2;
  const centerLon = (Math.min(...longitudes) + Math.max(...longitudes)) / 2;

  return (
    <MapContainer center={[centerLat, centerLon]} zoom={4} style={{ height: "90%", width: "100%" }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {points.map((p, index) => {
        if (p.latitude == null || p.longitude == null) return null;

        const isSelected = selectedFloat === p.float_id;

        return (
          <CircleMarker
            key={`${p.float_id}-${index}`}
            center={[p.latitude, p.longitude]}
            radius={isSelected ? 12 : 6}
            pathOptions={{
              color: isSelected ? '#ff4d4d' : '#36a2eb',
              fillColor: isSelected ? '#ff4d4d' : '#36a2eb',
              fillOpacity: 0.8,
            }}
            eventHandlers={{
              click: () => {
                // Toggle selection
                onSelectFloat(isSelected ? null : p.float_id);
              },
            }}
          >
            <Tooltip>
              Float ID: {p.float_id}<br />
              {p.value != null ? `Value: ${p.value.toFixed(2)}` : ''}
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
