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
import numpy

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
		return self._GetStep(direction)

	def _GetStep(self, index):
		index = numpy.clip(index, 0, self._StepVals.numSamples - 1)
		return tdu.Vector(
			self._StepVals['x'][index],
			self._StepVals['y'][index],
			self._StepVals['z'][index],
		)

	@property
	def _Steps(self):
		return [self._GetStep(i) for i in range(self._StepVals.numSamples)]

	def _GetNextStep(self):
		if not self._ShouldGoToTarget:
			return self._GetRandomStep()
		pos = self.Position
		targetpos = self._TargetPosition
		currentdist = (targetpos - pos).length()
		if self.comp.par.Stayattarget and currentdist <= self.comp.par.Targetradius:
			# self._LogEvent('_GetNextStep() - stopped near target')
			return None
		# self._LogEvent('_GetNextStep() - seeking target %r' % targetpos)
		steps = self._Steps
		random.shuffle(steps)
		for step in steps:
			newpos = pos + step
			newdist = (targetpos - newpos).length()
			if newdist <= currentdist:
				# self._LogEvent('_GetNextStep() - selecting step %r since it would move closer to target' % step)
				return step
		# self._LogEvent('_GetNextStep() - no steps would move closer to target, using random step')
		return steps[0]

	def TakeNextStep(self):
		step = self._GetNextStep()
		if step is not None:
			self.TakeStep(step)

