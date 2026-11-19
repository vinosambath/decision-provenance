---
title: Decision on Event Backbone
date: 2025-03-19
participants: [Priya Nair, Daniel Cho, Wei Lin, Ana Petrova]
---

Priya Nair: Alright, team, I think we’ve gone through the options for the event backbone pretty thoroughly. Shall we recap? 

Daniel Cho: Sure, we can’t use Kinesis because of that consumer group limit—way too restricting for our fan-out needs.

Wei Lin: And then RabbitMQ—no replay is a dealbreaker for us, right? The backfill requirement really puts it in the "nope" category.

Ana Petrova: Right, which brings us to SQS… Talk about a mess with ordering! We definitely can't risk messages dropping just because we wanted to keep things simple.

Priya Nair: Exactly, so that leaves us with Kafka, MSK. Any thoughts before we seal the deal?

Daniel Cho: I mean, it seems like the only logical choice left standing. If we don't go with Kafka, we’ll end up kicking ourselves later.

Wei Lin: Plus, it’s pretty scalable. I like that a lot. I mean, scalable solutions—who doesn’t love those?

Ana Petrova: Yeah, I just hope it doesn’t explode in our faces! But honestly, it seems like the safest bet given the alternatives.

Priya Nair: Agreed, and we’ll have to make sure we have enough resources. We'll have two platform engineers on this through Q3. 

Daniel Cho: Well, that's good—we need hands on deck for any potential hiccups.

Wei Lin: You mean like when we decided to pivot to microservices? Hiccup feels like an understatement there.

Ana Petrova: Haha, true! But hey, that's part of the job. At least we'll have Kafka to catch the incoming data streams, which is better than a safety net made of spaghetti!

Priya Nair: Okay, so no more debate then? Kafka’s it?

Daniel Cho: Yup, I say we lock it in.

Wei Lin: Let’s do it! Kafka all the way.

Ana Petrova: Sounds good to me. Get that set up!

Priya Nair: Great! I’ll send out the notes and rally the engineering team. Kafka it is.