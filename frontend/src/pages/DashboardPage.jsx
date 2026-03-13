import {
  Alert,
  AppBar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  FormControl,
  Grid,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  Tab,
  Tabs,
  TextField,
  Toolbar,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../api";

function CounterCard({ label, value }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h4" fontWeight={700}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}

const defaultSchemaYaml = `entity_name: ticket
version: 1
strategy: typed
fields:
  - name: client_reference
    type: string
    required: false
    description: External customer reference
    vectorize: false
`;

export default function DashboardPage() {
  const { me, logout } = useAuth();
  const [tab, setTab] = useState("overview");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const [tenant, setTenant] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [changes, setChanges] = useState([]);
  const [users, setUsers] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [manifests, setManifests] = useState([]);

  const [customerName, setCustomerName] = useState("");
  const [ticketTitle, setTicketTitle] = useState("");
  const [ticketDesc, setTicketDesc] = useState("");
  const [incidentTitle, setIncidentTitle] = useState("");
  const [incidentSeverity, setIncidentSeverity] = useState("sev3");
  const [changeTitle, setChangeTitle] = useState("");
  const [changeType, setChangeType] = useState("normal");
  const [changeRisk, setChangeRisk] = useState(5);
  const [schemaYaml, setSchemaYaml] = useState(defaultSchemaYaml);
  const [schemaResult, setSchemaResult] = useState("");

  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserFirstName, setNewUserFirstName] = useState("");
  const [newUserLastName, setNewUserLastName] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("ChangeMe123!");
  const [newUserRole, setNewUserRole] = useState("user");

  const isAdminSurface = useMemo(() => me?.role === "owner" || me?.role === "admin", [me]);

  const setMessage = (okMessage) => {
    setError("");
    setNotice(okMessage);
  };

  const setFailure = (err) => {
    setNotice("");
    const detail =
      err?.response?.data?.detail && typeof err.response.data.detail === "string"
        ? err.response.data.detail
        : "Request failed";
    setError(detail);
  };

  const loadData = async () => {
    const [tenantResp, customerResp, ticketResp, incidentResp, changeResp] = await Promise.all([
      api.get("/tenants/me"),
      api.get("/customers"),
      api.get("/tickets"),
      api.get("/incidents"),
      api.get("/changes"),
    ]);
    setTenant(tenantResp.data);
    setCustomers(customerResp.data);
    setTickets(ticketResp.data);
    setIncidents(incidentResp.data);
    setChanges(changeResp.data);

    if (isAdminSurface) {
      const [usersResp, permsResp, manifestsResp] = await Promise.all([
        api.get("/rbac/users"),
        api.get("/rbac/permissions"),
        api.get("/schema/manifests"),
      ]);
      setUsers(usersResp.data);
      setPermissions(permsResp.data);
      setManifests(manifestsResp.data);
    }
  };

  useEffect(() => {
    loadData().catch(setFailure);
  }, [isAdminSurface]);

  const createCustomer = async (event) => {
    event.preventDefault();
    if (!customerName.trim()) return;
    try {
      await api.post("/customers", { name: customerName, status: "active" });
      setCustomerName("");
      setMessage("Customer created");
      await loadData();
    } catch (err) {
      setFailure(err);
    }
  };

  const createTicket = async (event) => {
    event.preventDefault();
    if (!ticketTitle.trim()) return;
    try {
      await api.post("/tickets", {
        title: ticketTitle,
        description: ticketDesc,
        priority: "p3",
      });
      setTicketTitle("");
      setTicketDesc("");
      setMessage("Ticket created");
      await loadData();
    } catch (err) {
      setFailure(err);
    }
  };

  const createIncident = async (event) => {
    event.preventDefault();
    if (!incidentTitle.trim()) return;
    try {
      await api.post("/incidents", {
        title: incidentTitle,
        severity: incidentSeverity,
        status: "open",
      });
      setIncidentTitle("");
      setMessage("Incident created");
      await loadData();
    } catch (err) {
      setFailure(err);
    }
  };

  const createChange = async (event) => {
    event.preventDefault();
    if (!changeTitle.trim()) return;
    try {
      await api.post("/changes", {
        title: changeTitle,
        change_type: changeType,
        risk_score: Number(changeRisk),
      });
      setChangeTitle("");
      setMessage("Change request created");
      await loadData();
    } catch (err) {
      setFailure(err);
    }
  };

  const createUser = async (event) => {
    event.preventDefault();
    try {
      await api.post("/rbac/users", {
        email: newUserEmail,
        first_name: newUserFirstName,
        last_name: newUserLastName,
        password: newUserPassword,
        role: newUserRole,
      });
      setNewUserEmail("");
      setNewUserFirstName("");
      setNewUserLastName("");
      setMessage("User created");
      await loadData();
    } catch (err) {
      setFailure(err);
    }
  };

  const updateUserRole = async (userId, role) => {
    try {
      await api.patch(`/rbac/${userId}/role`, { role });
      setMessage("User role updated");
      await loadData();
    } catch (err) {
      setFailure(err);
    }
  };

  const toggleUserActive = async (userId, isActive) => {
    try {
      await api.patch(`/rbac/${userId}/active`, { is_active: !isActive });
      setMessage("User active state updated");
      await loadData();
    } catch (err) {
      setFailure(err);
    }
  };

  const planSchema = async () => {
    try {
      const response = await api.post("/schema/plan-yaml", { content: schemaYaml });
      setSchemaResult(JSON.stringify(response.data, null, 2));
      setMessage("Schema plan generated");
    } catch (err) {
      setFailure(err);
    }
  };

  const applySchema = async () => {
    try {
      const response = await api.post("/schema/apply-yaml", { content: schemaYaml });
      setSchemaResult(JSON.stringify(response.data, null, 2));
      setMessage("Schema applied");
      await loadData();
    } catch (err) {
      setFailure(err);
    }
  };

  return (
    <Box>
      <AppBar position="static">
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            MSP Platform
          </Typography>
          <Chip
            label={`${me?.first_name} ${me?.last_name} (${me?.role})`}
            variant="outlined"
            sx={{ color: "white", borderColor: "white" }}
          />
          <Button color="inherit" onClick={logout}>
            Sign Out
          </Button>
        </Toolbar>
      </AppBar>

      <Container sx={{ py: 3 }}>
        <Stack spacing={2}>
          <Typography variant="h5" fontWeight={700}>
            {tenant?.name || "Tenant"}
          </Typography>

          {notice && <Alert severity="success">{notice}</Alert>}
          {error && <Alert severity="error">{error}</Alert>}

          <Tabs value={tab} onChange={(_, value) => setTab(value)} variant="scrollable">
            <Tab value="overview" label="Overview" />
            <Tab value="operations" label="Operations" />
            {isAdminSurface && <Tab value="schema" label="Schema Controller" />}
            {isAdminSurface && <Tab value="rbac" label="RBAC Admin" />}
          </Tabs>

          {tab === "overview" && (
            <Stack spacing={2}>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 3 }}>
                  <CounterCard label="Customers" value={customers.length} />
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <CounterCard label="Tickets" value={tickets.length} />
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <CounterCard label="Incidents" value={incidents.length} />
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <CounterCard label="Changes" value={changes.length} />
                </Grid>
              </Grid>

              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">Create Customer</Typography>
                      <Box component="form" onSubmit={createCustomer}>
                        <Stack spacing={2} mt={2}>
                          <TextField
                            label="Customer Name"
                            value={customerName}
                            onChange={(e) => setCustomerName(e.target.value)}
                          />
                          <Button type="submit" variant="contained">
                            Add Customer
                          </Button>
                        </Stack>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid size={{ xs: 12, md: 6 }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">Create Ticket</Typography>
                      <Box component="form" onSubmit={createTicket}>
                        <Stack spacing={2} mt={2}>
                          <TextField
                            label="Title"
                            value={ticketTitle}
                            onChange={(e) => setTicketTitle(e.target.value)}
                          />
                          <TextField
                            label="Description"
                            multiline
                            minRows={2}
                            value={ticketDesc}
                            onChange={(e) => setTicketDesc(e.target.value)}
                          />
                          <Button type="submit" variant="contained">
                            Add Ticket
                          </Button>
                        </Stack>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Stack>
          )}

          {tab === "operations" && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">Incident Workflow</Typography>
                    <Box component="form" onSubmit={createIncident}>
                      <Stack spacing={2} mt={2}>
                        <TextField
                          label="Incident Title"
                          value={incidentTitle}
                          onChange={(e) => setIncidentTitle(e.target.value)}
                        />
                        <FormControl fullWidth>
                          <InputLabel id="incident-sev-label">Severity</InputLabel>
                          <Select
                            labelId="incident-sev-label"
                            value={incidentSeverity}
                            label="Severity"
                            onChange={(e) => setIncidentSeverity(e.target.value)}
                          >
                            <MenuItem value="sev1">SEV1</MenuItem>
                            <MenuItem value="sev2">SEV2</MenuItem>
                            <MenuItem value="sev3">SEV3</MenuItem>
                            <MenuItem value="sev4">SEV4</MenuItem>
                          </Select>
                        </FormControl>
                        <Button type="submit" variant="contained">
                          Create Incident
                        </Button>
                      </Stack>
                    </Box>
                    <List dense sx={{ mt: 2 }}>
                      {incidents.map((incident) => (
                        <ListItem key={incident.id} divider>
                          <ListItemText
                            primary={incident.title}
                            secondary={`${incident.severity} | ${incident.status}`}
                          />
                        </ListItem>
                      ))}
                      {!incidents.length && <Typography color="text.secondary">No incidents yet.</Typography>}
                    </List>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">Change Workflow</Typography>
                    <Box component="form" onSubmit={createChange}>
                      <Stack spacing={2} mt={2}>
                        <TextField
                          label="Change Title"
                          value={changeTitle}
                          onChange={(e) => setChangeTitle(e.target.value)}
                        />
                        <FormControl fullWidth>
                          <InputLabel id="change-type-label">Change Type</InputLabel>
                          <Select
                            labelId="change-type-label"
                            value={changeType}
                            label="Change Type"
                            onChange={(e) => setChangeType(e.target.value)}
                          >
                            <MenuItem value="standard">Standard</MenuItem>
                            <MenuItem value="normal">Normal</MenuItem>
                            <MenuItem value="emergency">Emergency</MenuItem>
                          </Select>
                        </FormControl>
                        <TextField
                          label="Risk Score (1-10)"
                          type="number"
                          value={changeRisk}
                          onChange={(e) => setChangeRisk(e.target.value)}
                        />
                        <Button type="submit" variant="contained">
                          Create Change
                        </Button>
                      </Stack>
                    </Box>
                    <List dense sx={{ mt: 2 }}>
                      {changes.map((change) => (
                        <ListItem key={change.id} divider>
                          <ListItemText
                            primary={change.title}
                            secondary={`${change.change_type} | ${change.status} | risk ${change.risk_score}`}
                          />
                        </ListItem>
                      ))}
                      {!changes.length && <Typography color="text.secondary">No change requests yet.</Typography>}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {tab === "schema" && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 7 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">Schema Controller (YAML)</Typography>
                    <Stack spacing={2} mt={2}>
                      <TextField
                        label="Schema YAML"
                        multiline
                        minRows={14}
                        value={schemaYaml}
                        onChange={(e) => setSchemaYaml(e.target.value)}
                      />
                      <Stack direction="row" spacing={1}>
                        <Button variant="outlined" onClick={planSchema}>
                          Plan
                        </Button>
                        <Button variant="contained" onClick={applySchema}>
                          Apply
                        </Button>
                      </Stack>
                      <TextField
                        label="Result"
                        multiline
                        minRows={8}
                        value={schemaResult}
                        InputProps={{ readOnly: true }}
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 5 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">Applied Manifests</Typography>
                    <List dense sx={{ mt: 1 }}>
                      {manifests.map((manifest) => (
                        <ListItem key={manifest.id} divider>
                          <ListItemText
                            primary={`${manifest.entity_name} v${manifest.version}`}
                            secondary={`${manifest.strategy} | ${manifest.status}`}
                          />
                        </ListItem>
                      ))}
                      {!manifests.length && <Typography color="text.secondary">No manifests yet.</Typography>}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {tab === "rbac" && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">Create User</Typography>
                    <Box component="form" onSubmit={createUser}>
                      <Stack spacing={2} mt={2}>
                        <TextField
                          label="Email"
                          value={newUserEmail}
                          onChange={(e) => setNewUserEmail(e.target.value)}
                        />
                        <TextField
                          label="First Name"
                          value={newUserFirstName}
                          onChange={(e) => setNewUserFirstName(e.target.value)}
                        />
                        <TextField
                          label="Last Name"
                          value={newUserLastName}
                          onChange={(e) => setNewUserLastName(e.target.value)}
                        />
                        <TextField
                          label="Temporary Password"
                          value={newUserPassword}
                          onChange={(e) => setNewUserPassword(e.target.value)}
                        />
                        <FormControl fullWidth>
                          <InputLabel id="new-user-role">Role</InputLabel>
                          <Select
                            labelId="new-user-role"
                            value={newUserRole}
                            label="Role"
                            onChange={(e) => setNewUserRole(e.target.value)}
                          >
                            <MenuItem value="user">User</MenuItem>
                            <MenuItem value="admin">Admin</MenuItem>
                            {me?.role === "owner" && <MenuItem value="owner">Owner</MenuItem>}
                          </Select>
                        </FormControl>
                        <Button type="submit" variant="contained">
                          Create User
                        </Button>
                      </Stack>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">Users</Typography>
                    <List dense sx={{ mt: 1 }}>
                      {users.map((user) => (
                        <ListItem key={user.id} divider>
                          <Stack spacing={1} sx={{ width: "100%" }}>
                            <Typography variant="body2">
                              {user.first_name} {user.last_name} - {user.email}
                            </Typography>
                            <Stack direction="row" spacing={1}>
                              <FormControl size="small" sx={{ minWidth: 120 }}>
                                <Select
                                  value={user.role}
                                  onChange={(e) => updateUserRole(user.id, e.target.value)}
                                >
                                  <MenuItem value="user">User</MenuItem>
                                  <MenuItem value="admin">Admin</MenuItem>
                                  {me?.role === "owner" && <MenuItem value="owner">Owner</MenuItem>}
                                </Select>
                              </FormControl>
                              <Button
                                size="small"
                                variant="outlined"
                                onClick={() => toggleUserActive(user.id, user.is_active)}
                              >
                                {user.is_active ? "Deactivate" : "Activate"}
                              </Button>
                            </Stack>
                          </Stack>
                        </ListItem>
                      ))}
                    </List>
                    <Typography variant="h6" sx={{ mt: 2 }}>
                      Permission Matrix
                    </Typography>
                    <List dense>
                      {permissions.map((perm) => (
                        <ListItem key={`${perm.role}-${perm.permission}`} divider>
                          <ListItemText primary={`${perm.role}: ${perm.permission}`} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Stack>
      </Container>
    </Box>
  );
}

