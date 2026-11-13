import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setConcurrency(2);
Config.setOverwriteOutput(true);
Config.setTimeoutInMilliseconds(60000);
Config.setDelayRenderTimeoutInMilliseconds(60000);
