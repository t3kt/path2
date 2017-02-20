try:
	import common_base as base
except ImportError:
	try:
		import base
	except ImportError:
		import common.lib.base as base
try:
	import common_util as util
except ImportError:
	try:
		import util
	except ImportError:
		import common.lib.util as util

if False:
	try:
		from _stubs import *
	except ImportError:
		from common.lib._stubs import *

import random

class StepGen(base.Extension):
	def __init__(self, comp):
		super().__init__(comp)
		self._StepVals = self.comp.op('./step_vals')
		self._PosVals = self.comp.op('./set_pos')
		self._ActualPosVals = self.comp.op('./position_out')

	def _PrepareChannels(self):
		x, y, z = self._PosVals['x'], self._PosVals['y'], self._PosVals['z']
		if x is None or y is None or z is None:
			self._PosVals.clear()
			x = self._PosVals.appendChan('x')
			y = self._PosVals.appendChan('y')
			z = self._PosVals.appendChan('z')
		return x, y, z

	def Reset(self):
		self.Position = 0, 0, 0

	@property
	def _TargetPosition(self):
		return tdu.Position(
			self.comp.par.Targetposx.eval(),
			self.comp.par.Targetposy.eval(),
			self.comp.par.Targetposz.eval(),
		)

	@property
	def Position(self):
		return tdu.Position(
			self._ActualPosVals['x'][0],
			self._ActualPosVals['y'][0],
			self._ActualPosVals['z'][0],
		)

	@Position.setter
	def Position(self, pos):
		x, y, z = self._PrepareChannels()
		x[0], y[0], z[0] = pos

	@property
	def _ShouldGoToTarget(self):
		if not self.comp.par.Targetenabled:
			return False
		chance = self.comp.par.Targetchance.eval()
		return chance >= 1 or random.random() >= chance

	@property
	def _IsAtTarget(self):
		pos = self.Position
		targetpos = self._TargetPosition
		diff = pos - targetpos
		dist = diff.length()
		return dist <= self.comp.par.Targetradius.eval()

	def TakeStep(self, step):
		self.Position = self.Position + step

	def _GetRandomStep(self):
		direction = random.randrange(self._StepVals.numSamples)
		return tdu.Vector(
			self._StepVals['x'][direction],
			self._StepVals['y'][direction],
			self._StepVals['z'][direction],
		)

	def _ChooseDirection(self):
		if not self._ShouldGoToTarget:
			return self._GetRandomStep()
		else:
			raise NotImplementedError()

	def Step(self):
		step = self._ChooseDirection()
		self.TakeStep(step)

