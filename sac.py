"""
To see Tensorboard:

tensorboard --logdir ./models
"""

import yaml
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import (
    CallbackList,
    EvalCallback,
)

from poker_env import PokerEnv
from utils.custom_callbacks import SelfPlayCallback


train = True
continue_training = False
training_timestamps = 1000000
current_model_version = "v10"

learning_starts = 30000

with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

env = PokerEnv(config=config["sac-six-player"], debug=False)
eval_env = PokerEnv(config=config["sac-six-player"])

model_path = f"models/sac/{current_model_version}/3500000"
if train:
    eval_env = PokerEnv(config=config["sac-six-player"])
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=f"models/sac/{current_model_version}/{training_timestamps}_log",
        log_path=f"models/sac/{current_model_version}/{training_timestamps}_log",
        n_eval_episodes=100,
        eval_freq=3000,
        deterministic=False,
        render=False,
    )

    event_callback = SelfPlayCallback(
        f"models/sac/{current_model_version}/{training_timestamps}_log/best_model.zip",
        rolling_starts=learning_starts,
    )
    callbacks = CallbackList([eval_callback, event_callback])

    if not continue_training:
        model = SAC(
            "MlpPolicy",
            env,
            verbose=1,
            learning_starts=learning_starts,
            learning_rate=0.00007,
            train_freq=(5, "episode"),
            tensorboard_log=f"models/sac/{current_model_version}/{training_timestamps}_tensorboard",
        )
    else:
        model: SAC = SAC.load(model_path, env=env)
        model.load_replay_buffer(
            f"models/sac/{current_model_version}/{training_timestamps}_replay_buffer"
        )
    model.learn(
        total_timesteps=training_timestamps,
        log_interval=3000,
        callback=callbacks,
        reset_num_timesteps=True,
    )
    model.save(f"models/sac/{current_model_version}/{training_timestamps}")
    model.save_replay_buffer(
        f"models/sac/{current_model_version}/{training_timestamps}_replay_buffer"
    )

else:
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
