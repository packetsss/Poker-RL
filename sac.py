"""
To see Tensorboard:

tensorboard --logdir .\tensorboard\sac\
"""

import yaml
import datetime
import torch as T
import numpy as np
from stable_baselines3 import SAC, TD3, PPO, A2C
from stable_baselines3.common.callbacks import EvalCallback

from poker_env import PokerEnv


with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

env = PokerEnv(config=config["sac-six-player"], debug=False)
eval_env = PokerEnv(config=config["sac-six-player"])

training_timestamps = 1000000
train = True
if train:
    eval_env = PokerEnv(config=config["sac-six-player"])
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=f"logs/{datetime.datetime.now().strftime('%m-%d %H.%M')}",
        log_path=f"logs/{datetime.datetime.now().strftime('%m-%d %H.%M')}",
        n_eval_episodes=100,
        eval_freq=500,
        deterministic=False,
        render=False,
    )

    model = SAC(
        "MlpPolicy",
        env,
        verbose=1,
        learning_starts=10000,
        train_freq=(2, "episode"),
        tensorboard_log="tensorboard/sac",
    )
    model.learn(
        total_timesteps=training_timestamps, log_interval=10000, callback=eval_callback
    )
    model.save(f"models/sac_{training_timestamps}")
else:
    model_path = f"models/sac_{training_timestamps}"  # "logs/best_model"  #
    model = SAC.load(model_path, env=env)

    obs = env.reset()
    while True:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        if done:
            obs = env.reset()

            print(
                f"\nprev chips: {tuple(env.previous_chips.values())}",
                f"\nchips: {tuple([x.chips for x in env.game.players])}",
                f"\nsum chips: {sum(tuple([x.chips for x in env.game.players]))}",
                f"\nwinners: {info}",
                f"\nbuyin history: {tuple(env.game.total_buyin_history.values())}",
                f"\nrestart times: {env.game.game_restarts}",
                "\n",
            )
