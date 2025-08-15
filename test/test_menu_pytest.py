#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import requests
import uuid

API_URL = "http://127.0.0.1:8080/chat"

class TestMenuFunctionality:
    """Test suite for menu functionality using pytest"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.session_id = str(uuid.uuid4())
        
    def _make_request(self, input_text):
        """Helper method to make API requests"""
        response = requests.post(API_URL, json={
            "input": input_text,
            "session_id": self.session_id
        }, timeout=20)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        return data.get("response", "")
    
    def test_greeting_shows_menu(self):
        """Test that greeting shows the menu options"""
        response = self._make_request("hola")
        
        # Check that it contains María introduction
        assert "maría" in response.lower(), "Should contain María introduction"
        
        # Check that it contains menu options
        assert "selecciona" in response.lower(), "Should contain selection prompt"
        assert "1️⃣" in response, "Should contain option 1"
        assert "2️⃣" in response, "Should contain option 2" 
        assert "3️⃣" in response, "Should contain option 3"
        assert "4️⃣" in response, "Should contain option 4"
        
        # Check menu option descriptions
        assert "domos" in response.lower(), "Should mention domos"
        assert "servicios" in response.lower(), "Should mention servicios"
        assert "disponibilidad" in response.lower(), "Should mention disponibilidad"
        
    def test_menu_request_shows_menu(self):
        """Test that asking for menu shows the menu options"""
        response = self._make_request("Tienes menus con los que me pueda guiar?")
        
        # Should trigger the MenuPrincipal tool
        assert "maría" in response.lower(), "Should contain María introduction"
        assert "1️⃣" in response, "Should contain menu options"
        assert "brillo de luna" in response.lower(), "Should contain glamping name"
        
    def test_menu_option_1_domos(self):
        """Test menu option 1 (Domos)"""
        # First show menu
        self._make_request("hola")
        
        # Then select option 1
        response = self._make_request("1")
        
        assert "domos" in response.lower(), "Should contain domos information"
        assert any(domo in response.lower() for domo in ["antares", "sirius", "centaury", "polaris"]), "Should mention specific domos"
        
    def test_menu_option_2_servicios(self):
        """Test menu option 2 (Servicios)"""
        self._make_request("hola")
        response = self._make_request("2")
        
        assert "servicios" in response.lower(), "Should contain services information"
        
    def test_menu_option_3_disponibilidad(self):
        """Test menu option 3 (Disponibilidad)"""
        self._make_request("hola")
        response = self._make_request("3")
        
        assert "disponibilidad" in response.lower(), "Should contain availability information"
        assert "fechas" in response.lower(), "Should mention dates"
        
    def test_menu_option_4_informacion(self):
        """Test menu option 4 (Información General)"""
        self._make_request("hola")
        response = self._make_request("4")
        
        # Should contain general information
        assert len(response) > 50, "Should provide substantial information"
        
    def test_menu_variations(self):
        """Test different ways to ask for menu"""
        menu_requests = [
            "menu",
            "menú",
            "opciones",
            "ayuda",
            "qué puedo hacer",
            "navegación",
            "guía"
        ]
        
        for request in menu_requests:
            # Use new session for each request
            session_id = str(uuid.uuid4())
            response = requests.post(API_URL, json={
                "input": request,
                "session_id": session_id
            }, timeout=20)
            
            if response.status_code == 200:
                data = response.json().get("response", "")
                # Should contain menu elements (either direct menu or helpful response)
                has_menu_elements = any(indicator in data.lower() for indicator in [
                    "1️⃣", "maría", "opciones", "domos", "servicios", "disponibilidad"
                ])
                
                assert has_menu_elements, f"Request '{request}' should trigger menu or helpful response"

if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])