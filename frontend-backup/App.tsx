import React from "react";
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import {
  ChakraProvider,
  Box,
  Flex,
  VStack,
  Heading,
  Text,
} from "@chakra-ui/react";

// Pages
import Dashboard from "./pages/Dashboard";
import Trades from "./pages/Trades";
import Settings from "./pages/Settings";
import Analytics from "./pages/Analytics";

// Components
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import StatusBar from "./components/StatusBar";

function App() {
  return (
    <ChakraProvider>
      <Router>
        <Box minH="100vh" bg="gray.100">
          <Flex>
            {/* Sidebar */}
            <Box w="250px" bg="white" minH="100vh" boxShadow="sm">
              <Sidebar />
            </Box>

            {/* Main Content */}
            <Box flex="1">
              <Header />

              <Box p="6">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/trades" element={<Trades />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/analytics" element={<Analytics />} />
                </Routes>
              </Box>

              {/* Status Bar */}
              <Box position="fixed" bottom="0" right="0" left="250px">
                <StatusBar />
              </Box>
            </Box>
          </Flex>
        </Box>
      </Router>
    </ChakraProvider>
  );
}

export default App;
