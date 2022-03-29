"""
To see Tensorboard:

tensorboard --logdir .\tensorboard\sac\
"""

import yaml
import datetime
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import EvalCallback

from poker_env import PokerEnv

train = True
training_timestamps = 1500000

current_model_version = "v5"

with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

env = PokerEnv(config=config["sac-six-player"], debug=False)
eval_env = PokerEnv(config=config["sac-six-player"])

if train:
    eval_env = PokerEnv(config=config["sac-six-player"])
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=f"logs/{datetime.datetime.now().strftime('%m-%d %H.%M')}",
        log_path=f"logs/{datetime.datetime.now().strftime('%m-%d %H.%M')}",
        n_eval_episodes=100,
        eval_freq=3000,
        deterministic=False,
        render=False,
    )

    model = SAC(
        "MlpPolicy",
        env,
        verbose=1,
        learning_starts=50000,
        learning_rate=0.00007,
        train_freq=(1, "episode"),
        tensorboard_log="tensorboard/sac",
    )
    model.learn(
        total_timesteps=training_timestamps, log_interval=3000, callback=eval_callback
    )
    model.save(f"models/sac/{current_model_version}/{training_timestamps}")
else:
    model_path = f"models/sac/{current_model_version}/1000000"  # "logs/best_model"  #
    model = SAC.load(model_path, env=env)

    obs = env.reset()
    while True:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action, get_all_rewards=True)
        if done:
            obs = env.reset()

            print(
                f"\nprev chips: {tuple(env.previous_chips.values())}",
                f"\nchips: {tuple([x.chips for x in env.game.players])}",
                f"\nsum chips: {sum(tuple([x.chips for x in env.game.players]))}",
                f"\nreward: {tuple(reward.values())}",
                f"\nwinners: {info}",
                f"\nbuyin history: {tuple(env.game.total_buyin_history.values())}",
                f"\nrestart times: {env.game.game_restarts}",
                "\n",
            )
