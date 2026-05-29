import { useState, useEffect } from "react";
import { Container, Row, Col, Card, Tabs, Tab, Table, Spinner } from "react-bootstrap";
import ChatBox from "./components/ChatBox";
import Chart from "./components/Chart";
import Map from "./components/Map";

export default function App() {
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFloat, setSelectedFloat] = useState(null);

  useEffect(() => {
    if (response && response.table && !response.map) {
      const mapData = response.table.map(item => ({
        latitude: item.latitude,
        longitude: item.longitude,
        float_id: item.float_id,
        value: item.temperature || item.salinity || item.pressure,
      }));
      setResponse(prevResponse => ({
        ...prevResponse,
        map: mapData,
      }));
    }
  }, [response]);

  // Reset selected float when a new response comes in
  useEffect(() => {
    setSelectedFloat(null);
  }, [response]);

  const renderTable = () => {
    if (!response?.table || response.table.length === 0) {
      return <p>No table data available.</p>;
    }

    const headers = Object.keys(response.table[0]);

    return (
      <Table striped bordered hover responsive size="sm">
        <thead>
          <tr>
            {headers.map(header => <th key={header}>{header}</th>)}
          </tr>
        </thead>
        <tbody>
          {response.table.map((row, index) => (
            <tr key={index} className={selectedFloat === row.float_id ? 'table-primary' : ''}>
              {headers.map(header => <td key={header}>{row[header]}</td>)}
            </tr>
          ))}
        </tbody>
      </Table>
    );
  };

  return (
    <Container fluid className="vh-100 d-flex flex-column p-3">
      <h1 className="mb-4 text-center">FloatChat</h1>
      <Row className="flex-grow-1">
        {/* LEFT - Chat Panel */}
        <Col md={4} className="d-flex flex-column">
          <Card className="h-100">
            <Card.Header as="h5">Chat</Card.Header>
            <Card.Body className="d-flex flex-column">
              <ChatBox
                onResponse={setResponse}
                loading={loading}
                setLoading={setLoading}
                setError={setError}
              />
            </Card.Body>
          </Card>
        </Col>

        {/* RIGHT - Visualization Panel */}
        <Col md={8}>
          <Card className="h-100">
            <Card.Header as="h5">Visualization Panel</Card.Header>
            <Card.Body>
              {loading && (
                <div className="text-center">
                  <Spinner animation="border" role="status" />
                  <p className="mt-2">Loading visualizations...</p>
                </div>
              )}
              {error && <p className="text-danger">{error}</p>}
              
              {!response && !loading && !error && (
                <div className="text-center">
                  <h2>Welcome to FloatChat</h2>
                  <p>Ask a question about oceanographic data to get started.</p>
                </div>
              )}

              {response && !loading && (
                <Tabs defaultActiveKey="map" id="viz-tabs" className="mb-3" mountOnEnter onSelect={() => setSelectedFloat(null)}>
                  {response.map && (
                    <Tab eventKey="map" title="Map">
                      <Map 
                        points={response.map} 
                        selectedFloat={selectedFloat}
                        onSelectFloat={setSelectedFloat}
                      />
                    </Tab>
                  )}
                  {response.chart && (
                    <Tab eventKey="chart" title="Chart">
                      <Chart 
                        data={response.chart} 
                        selectedFloat={selectedFloat}
                      />
                    </Tab>
                  )}
                  {response.table && (
                     <Tab eventKey="table" title="Data Table">
                      {renderTable()}
                    </Tab>
                  )}
                </Tabs>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}
