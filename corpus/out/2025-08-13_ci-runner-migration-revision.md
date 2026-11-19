---
title: Revisiting GitHub Actions Strategy
date: 2025-08-13
participants: [Sofia Torres, Jon Baptiste, Marcus Webb, Nadia Ibrahim]
---

Sofia Torres: Alright team, let’s dive back into GitHub Actions. It’s been a couple of months since we committed to it, and I feel like we need to reassess.

Jon Baptiste: Yeah, I mean, I think we were all a little too quick to jump on the hosted runner bandwagon. I’ve been watching the GPU test results, and it’s not pretty.

Marcus Webb: The GPU tests are just a unique beast, aren’t they? They seem to throw the whole pipeline into a tailspin. 

Nadia Ibrahim: Exactly. I mean, we set out to streamline things, not turn them into a circus. The hosted runners are fine for most stuff, but the GPU testing — oh boy.

Sofia Torres: So, are we thinking we might need self-hosted runners just for those? 

Jon Baptiste: I’m leaning that way. I mean, it would let us have more control over the environment. Plus, it’d be nice not to worry about parallel execution limits that hosted runners impose.

Marcus Webb: Right! And if we lose time on these tests because of execution limits, it's like, what's the point? We have to wait for them to finish just to get a single feature validated.

Nadia Ibrahim: I can already hear the groans from the infrastructure team. “Self-hosted runners? Are you sure you want to go back to that?” 

Jon Baptiste: Yeah, I could use a little more coffee just to muster up the energy for that meeting.

Sofia Torres: Well, let’s arm ourselves with some data first. If we show them the test runtimes spiking due to hosted runners, it might just convince them.

Marcus Webb: Good call. I mean, they like numbers, right? Can’t argue with hard facts…unless you’re a politician.

Nadia Ibrahim: Or a math teacher. They can argue with absolute truths! Life’s a blast, isn’t it?

Jon Baptiste: Speaking of blasts, has anyone figured out why our integration tests keep failing? I thought that was wrapped up.

Sofia Torres: Oh, those? Different rabbit hole. I’ll add that to the agenda. We need to put the brakes on that chaos too.

Marcus Webb: So, back to the self-hosted idea — how many runners do we think we’d actually need? 

Nadia Ibrahim: I’d say at least two for our GPU tests. That way, we can hit parallel testing without running into scheduling nightmares.

Jon Baptiste: Yeah, plus we can easily scale up from there. Worst case, we find ourselves drowning in GPU tasks. 

Marcus Webb: Or we can just blame it all on Jon for suggesting it in the first place, right?

Sofia Torres: No way! We’re a team. We rise and fall together. Unless, of course, it’s a terrible idea… then it’s totally Jon’s fault.

Nadia Ibrahim: Sounds like a solid plan! Let’s get the data, present the case, and maybe work on some options for those GPUs. 

Jon Baptiste: Alright! So self-hosted for the GPUs, hosted for everything else? We can swing that, right?

Sofia Torres: Yup, let’s do that. This feels like the right direction!