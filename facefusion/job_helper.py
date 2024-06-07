import os

from facefusion.filesystem import is_directory


def get_step_output_path(job_id : str, step_index : int, output_path : str) -> str:
	if is_directory(output_path):
		return os.path.join(output_path, job_id + '-' + str(step_index))

	output_directory_path, file_name_with_extension = os.path.split(output_path)
	output_file_name, output_file_extension = os.path.splitext(file_name_with_extension)
	return os.path.join(output_directory_path, output_file_name + '-' + job_id + '-' + str(step_index) + output_file_extension)
