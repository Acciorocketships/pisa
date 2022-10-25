import torch
import wandb
import inspect
from sae.sae_new import AutoEncoder
from sae.baseline_tspn import AutoEncoder as AutoEncoderTSPN
from sae.baseline_dspn import AutoEncoder as AutoEncoderDSPN
from sae.baseline_rnn import AutoEncoder as AutoEncoderRNN
from visualiser import Visualiser

torch.set_printoptions(precision=2, sci_mode=False)
model_name = "sae_rand-{name}-{hidden_dim}"
model_name_n = "sae_rand-{name}-{hidden_dim}-{n}"
model_path_base = f"saved/{model_name}.pt"
fig_path_base = f"plots/{model_name_n}.pdf"

seed = 5

project = "sae-rand-eval"

def experiments():
	trials = {
		"sae": [{"model": AutoEncoder}],
		"rnn": [{"model": AutoEncoderRNN}],
		"dspn": [{"model": AutoEncoderDSPN}],
		"tspn": [{"model": AutoEncoderTSPN}],
	}
	default = {
		"hidden_dim": 96,
		"n": 8,
		"log": False,
	}
	for name, trial in trials.items():
		if not isinstance(trial, list):
			trial = [trial]
		for cfg in trial:
			config = default.copy()
			config.update(cfg)
			config["name"] = name
			run(**config)


def run(
			hidden_dim = 96,
			n = 16,
			dim = 6,
			max_n = 16,
			model = None,
			name = None,
			log = True,
			**kwargs,
		):

	if inspect.isclass(model):
		model = model(dim=dim, hidden_dim=hidden_dim, max_n=max_n, **kwargs)

	device = "cpu"
	if torch.cuda.is_available():
		device = "cuda:0"

	model = model.to(device=device)
	model.eval()

	config = kwargs
	config.update({"dim": dim, "hidden_dim": hidden_dim, "max_n": max_n})

	if log:
		wandb.init(
			entity="prorok-lab",
			project=project,
			group=name,
			config=config,
		)
	vis = Visualiser(visible=False)

	try:
		model_path = model_path_base.format(name=name, hidden_dim=config["hidden_dim"])
		model_state_dict = torch.load(model_path, map_location=device)
		model.load_state_dict(model_state_dict)
	except Exception as e:
		print(e)

	data_list = []
	size_list = []
	torch.manual_seed(seed)
	for i in range(64):
		x = torch.randn(n, dim)
		data_list.append(x)
		size_list.append(n)
	x = torch.cat(data_list, dim=0)
	sizes = torch.tensor(size_list)
	batch = torch.arange(sizes.numel()).repeat_interleave(sizes)

	x = x.to(device)
	batch = batch.to(device)

	xr, batchr = model(x, batch)

	x = x[batch==0]
	xr = xr[batchr==0]

	vis.reset()
	vis.show_objects(x.cpu().detach(), alpha=0.3, linestyle="dashed")
	vis.show_objects(xr.cpu().detach())
	plt = vis.render()
	vis.save(path=fig_path_base.format(name=name, hidden_dim=hidden_dim, n=int(n)))

	if log:
		wandb.log({"vis": plt})
		wandb.finish()


if __name__ == '__main__':
	experiments()
