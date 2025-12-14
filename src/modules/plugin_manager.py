"""
StructureMaster - Plugin Manager Module
Manages plugins for extending application functionality.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .logger import Logger


@dataclass
class PluginInfo:
    """Information about a plugin."""
    name: str
    version: str = '1.0.0'
    author: str = ''
    description: str = ''
    enabled: bool = True
    path: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'enabled': self.enabled,
            'path': self.path,
        }


class PluginBase(ABC):
    """
    Base class for all plugins.
    Plugins must inherit from this class.
    """
    
    # Plugin metadata (override in subclass)
    NAME = 'BasePlugin'
    VERSION = '1.0.0'
    AUTHOR = ''
    DESCRIPTION = ''
    
    def __init__(self, manager: 'PluginManager'):
        """
        Initialize plugin.
        
        Args:
            manager: Plugin manager instance
        """
        self.manager = manager
        self.logger = Logger.get_instance()
    
    @abstractmethod
    def on_load(self) -> None:
        """Called when plugin is loaded."""
        pass
    
    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass
    
    def on_scan_start(self, path: Path) -> None:
        """Called when a scan starts."""
        pass
    
    def on_scan_complete(self, result: Any) -> None:
        """Called when a scan completes."""
        pass
    
    def on_build_start(self, structure: Dict) -> None:
        """Called when a build starts."""
        pass
    
    def on_build_complete(self, result: Any) -> None:
        """Called when a build completes."""
        pass
    
    def on_export_start(self, format: str) -> None:
        """Called when an export starts."""
        pass
    
    def on_export_complete(self, result: Any) -> None:
        """Called when an export completes."""
        pass
    
    def get_info(self) -> PluginInfo:
        """Get plugin information."""
        return PluginInfo(
            name=self.NAME,
            version=self.VERSION,
            author=self.AUTHOR,
            description=self.DESCRIPTION,
            enabled=True,
            path='',
        )


class PluginManager:
    """
    Manages plugin loading, unloading, and hooks.
    """
    
    def __init__(self, plugins_dir: Optional[Path] = None):
        """
        Initialize plugin manager.
        
        Args:
            plugins_dir: Directory containing plugins
        """
        self.logger = Logger.get_instance()
        self.plugins_dir = plugins_dir or Path.cwd() / 'plugins'
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Loaded plugins
        self._plugins: Dict[str, PluginBase] = {}
        
        # Registered hooks
        self._hooks: Dict[str, List[Callable]] = {
            'scan_start': [],
            'scan_complete': [],
            'build_start': [],
            'build_complete': [],
            'export_start': [],
            'export_complete': [],
        }
    
    def discover_plugins(self) -> List[PluginInfo]:
        """
        Discover available plugins in plugins directory.
        
        Returns:
            List of PluginInfo for discovered plugins
        """
        discovered = []
        
        for item in self.plugins_dir.iterdir():
            if item.is_file() and item.suffix == '.py':
                if item.name.startswith('_'):
                    continue
                
                info = PluginInfo(
                    name=item.stem,
                    path=str(item),
                    enabled=item.stem in self._plugins,
                )
                discovered.append(info)
            
            elif item.is_dir() and (item / '__init__.py').exists():
                info = PluginInfo(
                    name=item.name,
                    path=str(item),
                    enabled=item.name in self._plugins,
                )
                discovered.append(info)
        
        return discovered
    
    def load_plugin(self, name: str) -> bool:
        """
        Load a plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            True if loaded successfully
        """
        if name in self._plugins:
            self.logger.warn(f"Plugin {name} already loaded")
            return True
        
        # Find plugin file
        plugin_file = self.plugins_dir / f"{name}.py"
        plugin_dir = self.plugins_dir / name / '__init__.py'
        
        if plugin_file.exists():
            module_path = plugin_file
        elif plugin_dir.exists():
            module_path = plugin_dir
        else:
            self.logger.error(f"Plugin {name} not found")
            return False
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(name, module_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load plugin: {name}")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginBase) and 
                    attr is not PluginBase):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                raise ValueError(f"No PluginBase subclass found in {name}")
            
            # Instantiate and register
            plugin = plugin_class(self)
            plugin.on_load()
            
            self._plugins[name] = plugin
            self._register_plugin_hooks(plugin)
            
            self.logger.info(f"Loaded plugin: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin {name}: {e}")
            return False
    
    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if unloaded successfully
        """
        if name not in self._plugins:
            return False
        
        try:
            plugin = self._plugins[name]
            plugin.on_unload()
            self._unregister_plugin_hooks(plugin)
            del self._plugins[name]
            
            self.logger.info(f"Unloaded plugin: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload plugin {name}: {e}")
            return False
    
    def load_all_plugins(self) -> int:
        """
        Load all available plugins.
        
        Returns:
            Number of plugins loaded
        """
        loaded = 0
        for info in self.discover_plugins():
            if self.load_plugin(info.name):
                loaded += 1
        return loaded
    
    def get_loaded_plugins(self) -> List[PluginInfo]:
        """Get list of loaded plugins."""
        return [plugin.get_info() for plugin in self._plugins.values()]
    
    def _register_plugin_hooks(self, plugin: PluginBase) -> None:
        """Register plugin's hook methods."""
        hook_methods = {
            'scan_start': plugin.on_scan_start,
            'scan_complete': plugin.on_scan_complete,
            'build_start': plugin.on_build_start,
            'build_complete': plugin.on_build_complete,
            'export_start': plugin.on_export_start,
            'export_complete': plugin.on_export_complete,
        }
        
        for hook_name, method in hook_methods.items():
            # Only register if method is overridden
            if method.__func__ is not getattr(PluginBase, f'on_{hook_name.replace("_", "_")}', None):
                self._hooks[hook_name].append(method)
    
    def _unregister_plugin_hooks(self, plugin: PluginBase) -> None:
        """Unregister plugin's hook methods."""
        for hook_list in self._hooks.values():
            hook_list[:] = [h for h in hook_list if h.__self__ is not plugin]
    
    def trigger_hook(self, hook_name: str, *args, **kwargs) -> None:
        """
        Trigger a hook.
        
        Args:
            hook_name: Name of the hook
            *args: Hook arguments
            **kwargs: Hook keyword arguments
        """
        if hook_name not in self._hooks:
            return
        
        for callback in self._hooks[hook_name]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in hook {hook_name}: {e}")
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """
        Register a custom hook callback.
        
        Args:
            hook_name: Hook name
            callback: Callback function
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)


# Create singleton instance
plugin_manager = PluginManager()
