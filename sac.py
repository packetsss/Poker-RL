import gym
import yaml
import torch as T
import numpy as np
from stable_baselines3 import SAC, TD3, PPO, A2C


from poker_env import PokerEnv

with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

env = PokerEnv(config=config["sac-six-player"])

## policy-kwargs: change last layer in network from relu to None/Dense
# policy_kwargs = dict(activation_fn=T.nn.ReLU, net_arch=[32, 32, 32, 32, 64])

# model = SAC("MlpPolicy", env, verbose=1, learning_starts=1000, train_freq=(2, "episode"),)#, policy_kwargs=policy_kwargs)
# model.learn(total_timesteps=20000, log_interval=500)
# model.save("models/sac_v1")


model = SAC.load(
    "models/sac_v1",
    env=env,
)

obs = env.reset()
while True:
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, done, info = env.step(action)
    if done:
        obs = env.reset()
        print(
            f"\nprev chips: {tuple(env.previous_chips.values())}",
            f"\nchips: {[x.chips for x in env.game.players]}",
            f"\nwinners: {info}",
            "\n",
        )