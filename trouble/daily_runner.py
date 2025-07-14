import json
from typing import Dict, List
from .log_config import get_logger
from trouble.etude_core import EtudeRegistry, Etude # Etude needed for type hint if not already via Registry
from trouble.fetchers import DailyEtudeResult, EtudeDailyStatus # Import the new result types

logger = get_logger(__name__)

def execute_daily_etude_tasks(registry: EtudeRegistry) -> Dict[str, Dict]:
    """
    Executes the daily tasks for all registered etudes by processing their resources.

    Args:
        registry: An EtudeRegistry instance with discovered etudes.

    Returns:
        A dictionary where keys are etude names and values are the
        dictionary representation of DailyEtudeResult for that etude.
    """
    all_etudes_results: Dict[str, DailyEtudeResult] = {}
    etudes_list: List[Etude] = registry.get_all_etudes()

    if not etudes_list:
        logger.warning("No etudes registered. Nothing to do for daily tasks.")
        return {}

    logger.info(f"Executing daily tasks for {len(etudes_list)} etudes...")

    for etude in etudes_list:
        logger.info(f"Processing daily resources for Etude: {etude.name}...")
        etude_actions_log: List[str] = []
        etude_data_dict: Dict[str, any] = {}
        overall_etude_status: EtudeDailyStatus = EtudeDailyStatus.OK # Assume OK until a failure or no-op

        try:
            resources_to_fetch = etude.get_daily_resources()
        except Exception as e:
            logger.error(f"Could not get daily resources for {etude.name}: {e}")
            etude_actions_log.append(f"Failed to retrieve resource list: {e}")
            all_etudes_results[etude.name] = DailyEtudeResult(
                status=EtudeDailyStatus.FAILED,
                data=None,
                actions_log=etude_actions_log
            )
            continue # Skip to next etude

        if not resources_to_fetch:
            etude_actions_log.append("No daily resources defined for this etude.")
            overall_etude_status = EtudeDailyStatus.NO_OP
            all_etudes_results[etude.name] = DailyEtudeResult(
                status=overall_etude_status,
                data=None,
                actions_log=etude_actions_log
            )
            logger.info(f"Etude {etude.name}: No daily resources to fetch.")
            continue

        num_successful_fetches = 0
        num_failed_fetches = 0

        for resource_name, fetcher_instance in resources_to_fetch:
            logger.debug(f"Fetching resource '{resource_name}' for {etude.name}...")
            try:
                success, fetched_data, error_message = fetcher_instance.fetch()
                if success:
                    etude_data_dict[resource_name] = fetched_data
                    etude_actions_log.append(f"Successfully fetched resource '{resource_name}'.")
                    num_successful_fetches += 1
                else:
                    etude_actions_log.append(f"Failed to fetch resource '{resource_name}': {error_message}")
                    etude_data_dict[resource_name] = None # Or some other error indicator
                    num_failed_fetches += 1
            except Exception as e:
                # This catches errors in the fetcher's fetch() method itself, if not handled internally by fetch()
                logger.error(f"UNEXPECTED ERROR during fetch for resource '{resource_name}': {e}")
                etude_actions_log.append(f"Unexpected error fetching resource '{resource_name}': {e}")
                etude_data_dict[resource_name] = None
                num_failed_fetches += 1

        if num_failed_fetches > 0:
            if num_successful_fetches > 0:
                overall_etude_status = EtudeDailyStatus.PARTIAL_SUCCESS
            else:
                overall_etude_status = EtudeDailyStatus.FAILED
        elif num_successful_fetches == 0 and not resources_to_fetch: # Should be caught by earlier check
             overall_etude_status = EtudeDailyStatus.NO_OP
        # If all successful and resources_to_fetch was not empty, status remains OK.


        all_etudes_results[etude.name] = DailyEtudeResult(
            status=overall_etude_status,
            data=etude_data_dict if etude_data_dict else None, # Store None if no data was successfully fetched or defined
            actions_log=etude_actions_log
        )
        logger.info(f"Finished processing for {etude.name}. Status: {overall_etude_status.value}")

    # Convert DailyEtudeResult objects to dictionaries for JSON serialization
    # NamedTuples are often directly serializable, but their _asdict() method is canonical.
    # However, Enum status needs to be value for JSON.
    final_output_dict: Dict[str, Dict] = {}
    for name, result in all_etudes_results.items():
        final_output_dict[name] = {
            "status": result.status.value, # Use enum value for JSON
            "data": result.data,
            "actions_log": result.actions_log
        }

    return final_output_dict
