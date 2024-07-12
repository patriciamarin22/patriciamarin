from time import sleep
from typing import Optional, Tuple

import gradio

from facefusion import logger, process_manager, state_manager, wording
from facefusion.common_helper import get_first
from facefusion.core import process_step
from facefusion.jobs import job_manager, job_runner
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import register_ui_component
from facefusion.uis.typing import JobRunnerAction
from facefusion.uis.ui_helper import convert_str_none

JOB_RUNNER_WRAPPER : Optional[gradio.Column] = None
JOB_RUNNER_JOB_ACTION_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_RUNNER_JOB_ID_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_RUNNER_START_BUTTON : Optional[gradio.Button] = None
JOB_RUNNER_STOP_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_RUNNER_WRAPPER
	global JOB_RUNNER_JOB_ACTION_DROPDOWN
	global JOB_RUNNER_JOB_ID_DROPDOWN
	global JOB_RUNNER_START_BUTTON
	global JOB_RUNNER_STOP_BUTTON

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		is_job_runner = state_manager.get_item('ui_workflow') == 'job_runner'
		queued_job_ids = job_manager.find_job_ids('queued') or [ 'none' ]

		with gradio.Column(visible = is_job_runner) as JOB_RUNNER_WRAPPER:
			JOB_RUNNER_JOB_ACTION_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.job_runner_job_action_dropdown'),
				choices = uis_choices.job_runner_actions,
				value = get_first(uis_choices.job_runner_actions)
			)
			JOB_RUNNER_JOB_ID_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.job_runner_job_id_dropdown'),
				choices = queued_job_ids,
				value = get_first(queued_job_ids)
			)
			with gradio.Row():
				JOB_RUNNER_START_BUTTON = gradio.Button(
					value = wording.get('uis.start_button'),
					variant = 'primary',
					size = 'sm'
				)
				JOB_RUNNER_STOP_BUTTON = gradio.Button(
					value = wording.get('uis.stop_button'),
					variant = 'primary',
					size = 'sm',
					visible = False
				)
		register_ui_component('job_runner_wrapper', JOB_RUNNER_WRAPPER)


def listen() -> None:
	JOB_RUNNER_JOB_ACTION_DROPDOWN.change(update_job_action, inputs = JOB_RUNNER_JOB_ACTION_DROPDOWN, outputs = JOB_RUNNER_JOB_ID_DROPDOWN)
	JOB_RUNNER_START_BUTTON.click(start, outputs = [ JOB_RUNNER_START_BUTTON, JOB_RUNNER_STOP_BUTTON ])
	JOB_RUNNER_START_BUTTON.click(run, inputs = [ JOB_RUNNER_JOB_ACTION_DROPDOWN, JOB_RUNNER_JOB_ID_DROPDOWN ], outputs = [ JOB_RUNNER_START_BUTTON, JOB_RUNNER_STOP_BUTTON, JOB_RUNNER_JOB_ID_DROPDOWN ])
	JOB_RUNNER_STOP_BUTTON.click(stop, outputs = [ JOB_RUNNER_START_BUTTON, JOB_RUNNER_STOP_BUTTON ])


def start() -> Tuple[gradio.Button, gradio.Button]:
	while not process_manager.is_processing():
		sleep(0.5)
	return gradio.Button(visible = False), gradio.Button(visible = True)


def run(job_action : JobRunnerAction, job_id : str) -> Tuple[gradio.Button, gradio.Button, gradio.Dropdown]:
	job_id = convert_str_none(job_id)

	if job_action == 'job-run':
		logger.info(wording.get('running_job').format(job_id = job_id), __name__.upper())
		if job_runner.run_job(job_id, process_step):
			logger.info(wording.get('processing_job_succeed').format(job_id = job_id), __name__.upper())
		else:
			logger.info(wording.get('processing_job_failed').format(job_id = job_id), __name__.upper())
		queued_job_ids = job_manager.find_job_ids('queued') or [ 'none' ]
		return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Dropdown(value = get_first(queued_job_ids), choices = queued_job_ids)
	if job_action == 'job-run-all':
		logger.info(wording.get('running_jobs'), __name__.upper())
		if job_runner.run_jobs(process_step):
			logger.info(wording.get('processing_jobs_succeed'), __name__.upper())
		else:
			logger.info(wording.get('processing_jobs_failed'), __name__.upper())
	if job_action == 'job-retry':
		logger.info(wording.get('retrying_job').format(job_id = job_id), __name__.upper())
		if job_runner.retry_job(job_id, process_step):
			logger.info(wording.get('processing_job_succeed').format(job_id = job_id), __name__.upper())
		else:
			logger.info(wording.get('processing_job_failed').format(job_id = job_id), __name__.upper())
		failed_job_ids = job_manager.find_job_ids('failed') or [ 'none' ]
		return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Dropdown(value = get_first(failed_job_ids), choices = failed_job_ids)
	if job_action == 'job-retry-all':
		logger.info(wording.get('retrying_jobs'), __name__.upper())
		if job_runner.retry_jobs(process_step):
			logger.info(wording.get('processing_jobs_succeed'), __name__.upper())
		else:
			logger.info(wording.get('processing_jobs_failed'), __name__.upper())
	return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Dropdown(value = None, choices = None)


def stop() -> Tuple[gradio.Button, gradio.Button]:
	process_manager.stop()
	return gradio.Button(visible = True), gradio.Button(visible = False)


def update_job_action(job_action : JobRunnerAction) -> gradio.Dropdown:
	queued_job_ids = job_manager.find_job_ids('queued') or [ 'none' ]
	failed_job_ids = job_manager.find_job_ids('failed') or [ 'none' ]

	if job_action == 'job-run':
		return gradio.Dropdown(value = get_first(queued_job_ids), choices = queued_job_ids, visible = True)
	if job_action == 'job-retry':
		return gradio.Dropdown(value = get_first(failed_job_ids), choices = failed_job_ids, visible = True)
	return gradio.Dropdown(value = 'none', choices = [ 'none' ], visible = False)