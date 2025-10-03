import { useState, useContext } from "react";
import {
  AppBar,
  Toolbar,
  IconButton,
  Drawer,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import HomeIcon from "@mui/icons-material/Home";
import PeopleIcon from "@mui/icons-material/People";
import SecurityIcon from "@mui/icons-material/Security";
import AssessmentIcon from "@mui/icons-material/Assessment";
import SettingsIcon from "@mui/icons-material/Settings";
import LogoutIcon from "@mui/icons-material/Logout";
import LightModeIcon from "@mui/icons-material/LightMode";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import VideocamIcon from "@mui/icons-material/Videocam";
import ThreeSixtyIcon from "@mui/icons-material/ThreeSixty";
import { Link as RouterLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ColorModeContext } from "../theme";
import mrdLogo from '../assets/images/main-logo.png';

// Definimos las entradas básicas del menú
const baseMenu = [
  { text: "Inicio",   icon: <HomeIcon />,   to: "/" },
  { text: "Control de Cámara", icon: <VideocamIcon />, to: "/camara" },
  { text: "Análisis de Coples", icon: <AssessmentIcon />, to: "/analisis" },
  { text: "Rutina de Inspección", icon: <ThreeSixtyIcon />, to: "/rutina-inspeccion" },
  { text: "Configuraciones", icon: <SettingsIcon />, to: "/analisis/configuraciones" },
  { text: "Usuarios", icon: <PeopleIcon />, to: "/usuarios" },
];

export default function Layout() {
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  const { user, logout } = useAuth();
  const { toggleColorMode } = useContext(ColorModeContext);

  // Construimos el menú: si es Super Administrador, añadimos Roles
  const menuItems = [
    ...baseMenu,
    ...(user?.rol_nombre === 'Super Administrador'
      ? [{ text: "Roles", icon: <SecurityIcon />, to: "/roles" }]
      : []
    ),
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <AppBar position='fixed' sx={{ zIndex: theme.zIndex.drawer + 1, bgcolor: 'appbar_azul.main' }}>
        <Toolbar>
          <IconButton color='inherit' edge='start' onClick={() => setOpen(o => !o)} sx={{ mr: 2 }}>
            <MenuIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }} />
          <IconButton color='inherit' onClick={toggleColorMode} sx={{ mr: 1 }}>
            {theme.palette.mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
          <IconButton color='inherit' onClick={logout}>
            <LogoutIcon />
          </IconButton>
          <Box component="img" src={mrdLogo} alt="Asistente Controla Logo" sx={{ height: 40, ml: 2 }} />
        </Toolbar>
      </AppBar>

      <Box sx={{ display: 'flex', flexGrow: 1 }}>
        <Drawer
          variant='temporary'
          open={open}
          onClose={() => setOpen(false)}
          ModalProps={{ keepMounted: true }}
          anchor='left'
          sx={{ '& .MuiDrawer-paper': {
            top: theme.mixins.toolbar.minHeight,
            height: `calc(100% - ${theme.mixins.toolbar.minHeight}px)`,
            width: 240,
            bgcolor: 'sidebar.main',
          } }}
        >
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant='subtitle1' noWrap>
              {user?.name}
            </Typography>
            <Typography variant='body2' color='text.secondary' noWrap>
              {user?.rol_nombre}
            </Typography>
          </Box>
          <Divider />
          <List>
            {menuItems.map(({ text, icon, to }) => (
              <ListItem
                key={text}
                component={RouterLink}
                to={to}
                onClick={() => setOpen(false)}
              >
                <ListItemIcon sx={{ color: 'sidebar.icon' }}>{icon}</ListItemIcon>
                <ListItemText primary={text} sx={{ color: 'sidebar.texto' }} />
              </ListItem>
            ))}
          </List>
        </Drawer>

        <Box
          component='main'
          sx={{
            flex: '1 1 auto',
            minHeight: 0,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            filter: open ? 'blur(4px)' : 'none',
            transition: 'filter 0.3s ease-out',
            px: 4,
            py: 2,
          }}
        >
          <Toolbar />
          <Outlet />
        </Box>
      </Box>

      <Box component='footer' sx={{ py: 1, px: 2, bgcolor: 'footer.main', textAlign: 'center' }}>
        <Typography variant='caption'>
          © {new Date().getFullYear()} Tecnologías Controla S.A de C.V., Todos los derechos reservados.
        </Typography>
      </Box>
    </Box>
  );
}
