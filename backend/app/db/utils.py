from typing import Dict, Any, List


def dict_from_row(cursor, row) -> Dict[str, Any]:
	"""Convert a database row to a dictionary."""
	if not row:
		return {}
	return {cursor.description[i][0]: value for i, value in enumerate(row)}


def rows_to_dict_list(cursor, rows: List) -> List[Dict[str, Any]]:
	"""Convert multiple database rows to a list of dictionaries."""
	return [dict_from_row(cursor, row) for row in rows]