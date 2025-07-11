import abc
import importlib
import inspect
import os
import pkgutil
from typing import Type, Union, TypeVar

from typing import Type, Union, TypeVar, List, Tuple # Added List, Tuple
# It's better to import Fetcher directly if possible, to avoid string literals for type hints
# from trouble.fetchers import Fetcher # This will be problematic due to circular dependency if Fetcher also imports Etude
# So, we'll use a string literal for Fetcher type hint if Fetcher itself doesn't need to import Etude.
# If Fetcher *does* need Etude, one of them needs to use a string literal type hint for the other.
# Given Fetcher is more fundamental here, Etude will use string literal for 'Fetcher'.

# Forward declaration for type hinting EtudeRegistry within Etude
E = TypeVar('E', bound='Etude')


class Etude(abc.ABC):
    """
    Abstract base class for an Etude.
    Etude implementations should define NAME and DESCRIPTION as class attributes.
    """
    NAME: str = "Unnamed Etude"
    DESCRIPTION: str = "No description provided."

    def __init__(self, name: str, description: str):
        if not name or not isinstance(name, str):
            raise ValueError("Etude name must be a non-empty string.")
        if not isinstance(description, str):
            raise ValueError("Etude description must be a string.")
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @abc.abstractmethod
    def generate_content(self, output_dir: str, registry: 'EtudeRegistry') -> None:
        """
        Generates the HTML content for this etude into its specific subdirectory.
        Args:
            output_dir: The root directory for this etude's output (e.g., docs/etude_name/).
            registry: The EtudeRegistry instance, for accessing other etudes if needed.
        """
        pass

    @abc.abstractmethod
    def get_metrics(self, registry: 'EtudeRegistry') -> dict[str, any]:
        """
        Returns a dictionary of metrics for this etude.
        Args:
            registry: The EtudeRegistry instance, for accessing other etudes if needed.
        """
        pass

    def get_daily_resources(self) -> List[Tuple[str, 'Fetcher']]:
        """
        Returns a list of resources to be fetched daily for this etude.
        Each item in the list is a tuple: (resource_name: str, fetcher_instance: Fetcher).
        The default implementation returns an empty list.
        Etudes should override this to define their daily data sources.
        """
        return []

    def __repr__(self) -> str:
        return f"<Etude(name='{self.name}')>"


class EtudeRegistry:
    def __init__(self):
        self._etudes: dict[str, Etude] = {}

    def register_etude(self, etude_instance: Etude) -> None:
        if not isinstance(etude_instance, Etude):
            raise TypeError("Can only register instances of Etude.")
        if etude_instance.name in self._etudes:
            # Allowing re-registration for now, could be a warning or error
            print(f"Warning: Re-registering etude with name '{etude_instance.name}'.")
        self._etudes[etude_instance.name] = etude_instance

    def get_etude(self, name: str) -> Union[Etude, None]:
        return self._etudes.get(name)

    def get_all_etudes(self) -> list[Etude]:
        """Returns all etudes, with 'zero' first if it exists, then others alphabetically."""
        etudes_list = list(self._etudes.values())

        # Custom sort: 'zero' first, then alphabetical by name
        def sort_key(etude: Etude):
            if etude.name == 'zero':
                return (0, 'zero') # Sorts 'zero' first
            return (1, etude.name) # Sorts others alphabetically

        etudes_list.sort(key=sort_key)
        return etudes_list

    def discover_etudes(self, package_name: str = "trouble.etudes") -> None:
        """
        Discovers and registers Etude subclasses from the given package.
        Etude classes are expected to have NAME and DESCRIPTION class attributes.
        """
        print(f"Discovering etudes in package: {package_name}")
        try:
            package = importlib.import_module(package_name)
            base_path = package.__path__[0] # Get the filesystem path of the package
        except ImportError:
            print(f"Warning: Etude package '{package_name}' not found or has no __path__.")
            return
        except AttributeError: # package has no __path__ (e.g. it's a single file module)
             print(f"Warning: Etude package '{package_name}' is not a package with a directory structure.")
             return


        for item_name in os.listdir(base_path):
            item_path = os.path.join(base_path, item_name)
            if os.path.isdir(item_path) and not item_name.startswith('_'):
                # This directory is a potential etude sub-package (e.g., 'zero', 'one')
                etude_subpackage_name = f"{package_name}.{item_name}"

                # Convention: Look for an 'etude_impl.py' or similar within the sub-package
                # For now, let's try to import the sub-package itself, assuming its __init__.py
                # makes the Etude class available, or a specific module like 'etude_impl'.

                # Attempt to import 'etude_impl' from the subpackage
                module_to_try = f"{etude_subpackage_name}.etude_impl"
                try:
                    module = importlib.import_module(module_to_try)
                    print(f"  Inspecting module: {module_to_try}")
                    self._inspect_and_register_etudes_from_module(module)
                except ImportError:
                    # If 'etude_impl' is not found, try importing the subpackage's __init__
                    # (which might expose the Etude class)
                    print(f"    Module {module_to_try} not found. Trying to import {etude_subpackage_name} itself.")
                    try:
                        module = importlib.import_module(etude_subpackage_name)
                        print(f"  Inspecting module (package init): {etude_subpackage_name}")
                        self._inspect_and_register_etudes_from_module(module)
                    except ImportError as e_pkg:
                        print(f"    Could not import etude subpackage {etude_subpackage_name}: {e_pkg}")
                except Exception as e:
                    print(f"    Error processing module for {etude_subpackage_name}: {e}")

    def _inspect_and_register_etudes_from_module(self, module) -> None:
        """Helper to inspect a module and register Etude classes found within."""
        for attribute_name, attribute_value in inspect.getmembers(module):
            if inspect.isclass(attribute_value) and \
               issubclass(attribute_value, Etude) and \
               attribute_value is not Etude:

                etude_class_name = getattr(attribute_value, 'NAME', None)
                etude_class_description = getattr(attribute_value, 'DESCRIPTION', None)

                if not etude_class_name or not etude_class_description:
                    print(f"    Warning: Etude class {attribute_value.__name__} in {module.__name__} "
                          f"is missing NAME or DESCRIPTION class attributes. Skipping.")
                    continue

                try:
                    # Etude subclasses __init__ should call super with their NAME and DESCRIPTION.
                    instance = attribute_value()
                    self.register_etude(instance)
                    print(f"      Registered etude: {instance.name} (class: {attribute_value.__name__})")
                except Exception as e:
                    print(f"    Error instantiating or registering etude {attribute_value.__name__} "
                          f"from {module.__name__}: {e}")

# Example of how EtudeRegistry might be forward declared if Etude needed it directly
# EtudeRegistry = TypeVar('EtudeRegistry', bound='EtudeRegistry')
