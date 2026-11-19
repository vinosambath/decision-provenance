---
title: Event Backbone Discussion
date: 2025-03-05
participants: [Priya Nair, Daniel Cho, Wei Lin, Ana Petrova]
---

Priya Nair: Alright team, let’s dive into our options for the event backbone. I think we should start with Kafka, right? I mean, it seems pretty robust.

Daniel Cho: Definitely. Kafka is solid, but then again, I’ve been hearing mixed reviews—like, do we really want to manage our own MSK?

Wei Lin: Good point, I read somewhere it requires a bit of heavy lifting for scaling. Plus, it’s not as easy to handle as Kinesis, you know?

Ana Petrova: Kinesis is nice, but remember, it caps at five consumers per shard, which could be a problem for our fan-out requirements.

Daniel Cho: Right! That’s a serious limitation. What do we think about RabbitMQ? I mean, I've used it before and it feels pretty intuitive.

Priya Nair: Yeah, but the replay feature worries me. Without it, how do we handle backfills when necessary? We don’t want to end up doing everything manually.

Wei Lin: Exactly, and if we have to backfill a ton of data, it could really mess up our timelines. Oh, and SQS gives me pause too. The potential for ordering issues could throw a wrench in our plans.

Ana Petrova: Yeah, and we’ve already talked about how messages sometimes just… disappear. That’s not something we can afford, right?

Daniel Cho: So, I guess we’re leaning more towards Kafka then? Or are we just afraid of the alternatives?

Priya Nair: I think we’re just weighing the pros and cons. Like, what if we prototype with Kinesis? Get a feel for it under load and see if the consumer limits really break us?

Wei Lin: It does help that it’s easier to set up initially, but I’m still worried about that fan-out. Can we really afford to hit that ceiling too quickly?

Ana Petrova: We could mitigate with event batching or message deduplication… you know, get creative with how we architect around those limits? 

Daniel Cho: Creative solutions, huh? Sounds like your specialty, Ana! But I’m curious—what's our cut-off point? When do we decide enough is enough?

Priya Nair: Hmm, maybe after we get some benchmarks back from a proof-of-concept? I just don’t want to get too tunnel-visioned, you know?

Wei Lin: Agreed, let’s keep this exploratory. If we could mock some load tests on our candidates, like… what’s that tool, Locust? 

Ana Petrova: Oh, Locust would be perfect! That's easy to set up. So, let’s wrap this up by saying we’ll run some tests on Kinesis and Kafka first, and keep RabbitMQ in the discussion, just for fun?

Daniel Cho: Sounds good to me—let's keep digging into each option before we commit to anything.

Priya Nair: Alright, I’ll draft up some action items post-meeting. And we’ll circle back once we’ve got our results. 

Wei Lin: Can’t wait to see how this plays out!