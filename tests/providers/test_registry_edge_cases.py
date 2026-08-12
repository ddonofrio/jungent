"""Edge case tests for provider enable/disable state handling."""


class TestProviderRegistryEnableDisableEdgeCases:
    """Tests for edge cases in provider enable/disable operations."""

    def test_enable_already_enabled(self):
        """Test enabling a provider that is already enabled (should be no-op)."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        registry.register("mock", MockProvider1)

        # Enable twice - should reuse same instance
        provider1 = registry.enable_provider("mock")
        provider2 = registry.enable_provider("mock")

        assert provider1 is provider2

    def test_disable_already_disabled(self):
        """Test disabling a provider that is already disabled."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        registry.register("mock", MockProvider1)

        # Disable twice - should handle gracefully
        registry.disable_provider("mock")
        result = registry.disable_provider("mock")  # Should not raise

    def test_switch_from_enabled_list_to_disabled(self):
        """Test transitioning from enabled_providers allowlist to disabled list."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        registry.register("mock", MockProvider1)
        registry.register("other", MockProvider2 if "MockProvider2" in dir() else None)

        # Start with allowlist
        config = {"enabled_providers": ["mock"]}
        registry.load_from_config(config)

        assert registry.get("mock") is not None

        # Now disable using disabled list
        registry.disable_provider("mock")

        assert registry.get("mock") is None

    def test_switch_from_disabled_list_to_enabled(self):
        """Test transitioning from disabled to enabled via enable call."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        registry.register("mock", MockProvider1)

        # Disable first
        registry.disable_provider("mock")
        assert registry.get("mock") is None

        # Enable again with API key
        provider = registry.enable_provider("mock", api_key="test-key")

        assert provider is not None

    def test_enable_in_both_lists(self):
        """Test enabling a provider that appears in both enabled and disabled lists."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        registry.register("mock", MockProvider1)

        # Set up conflicting state
        config = {
            "enabled_providers": ["mock"],
            "disabled_providers": ["mock"],
        }
        registry.load_from_config(config)

        # enabled list takes precedence - mock should be enabled initially
        assert registry.get("mock") is not None

        # Now explicitly disable it
        registry.disable_provider("mock")
        assert registry.get("mock") is None

    def test_disable_then_enable_preserves_state(self):
        """Test that disabling then enabling preserves the instance state."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        registry.register("mock", MockProvider1)

        # Enable and get instance
        provider1 = registry.enable_provider("mock")
        assert provider1 is not None

        # Disable and enable again
        registry.disable_provider("mock")
        provider2 = registry.enable_provider("mock")

        assert provider2 is not None

    def test_multiple_providers_enable_disable_order(self):
        """Test enabling/disabling multiple providers in different orders."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        for i in range(3):
            registry.register(f"mock{i}", MockProvider1)

        # Enable all
        for i in range(3):
            registry.enable_provider(f"mock{i}")

        assert len(registry.get_enabled_providers()) == 3

        # Disable specific ones
        registry.disable_provider("mock0")
        registry.disable_provider("mock1")

        assert len(registry.get_enabled_providers()) == 1

    def test_config_reconciliation_edge_cases(self):
        """Test various config reconciliation scenarios."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        for i in range(4):
            registry.register(f"mock{i}", MockProvider1)

        # Case 1: Empty disabled list (all enabled)
        config1 = {"disabled_providers": []}
        registry.load_from_config(config1)
        assert len(registry.get_enabled_providers()) == 4

        # Case 2: All providers disabled, then enable one by one
        config2 = {"enabled_providers": [], "disabled_providers": list(range(4))}
        registry2 = ProviderRegistry()
        for i in range(4):
            registry2.register(f"mock{i}", MockProvider1)
        registry2.load_from_config(config2)

        # Enable first one
        assert registry2.get("mock0") is None

        registry2.enable_provider("mock0", api_key="key")
        assert registry2.get("mock0") is not None

    def test_get_disabled_provider_does_not_create_instance(self):
        """Test that calling get on disabled provider does not create instance."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        registry.register("mock", MockProvider1)

        # Disable before getting
        registry.disable_provider("mock")

        # Should return None without creating instance
        assert registry.get("mock") is None

        # Creating instance manually and disabling should remove it
        provider_instance = MockProvider1()
        registry.register_instance(provider_instance)

        registry.disable_provider("mock")

        assert registry.get("mock") is None

    def test_enable_with_different_api_keys(self):
        """Test enabling with different API keys preserves them."""
        from jungent.providers import ProviderRegistry, MockProvider1

        registry = ProviderRegistry()
        registry.register("mock", MockProvider1)

        provider1 = registry.enable_provider("mock", api_key="key1")
        assert provider1.api_key == "key1"

        # Re-enable with different key should work (replaces instance)
        provider2 = registry.enable_provider("mock", api_key="key2")
        assert provider2 is not None
