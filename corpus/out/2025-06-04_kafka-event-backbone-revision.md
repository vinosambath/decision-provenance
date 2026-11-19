---
title: Revisiting Kafka Commitments
date: 2025-06-04
participants: [Priya Nair, Daniel Cho, Wei Lin, Ana Petrova]
---

Priya Nair: Alright everyone, thanks for hopping on. I think it’s time we circle back to Kafka and see how everyone feels about our direction.

Daniel Cho: Yeah, I’ve been thinking about that. I mean, we jumped in pretty fast without really talking through the potential pitfalls. 

Wei Lin: Pitfalls? You mean like the time we tried to scale that database without proper load testing? *chuckles* 

Ana Petrova: *laughs* Let’s not go down that rabbit hole again! I just got over the last trauma. But seriously, Daniel, what are your concerns?

Daniel Cho: Mostly about scope. I feel like we bit off more than we can chew, especially with user events on top of the order topic. 

Priya Nair: So, are you suggesting we roll back on user events for now?

Wei Lin: Yeah, let’s not forget about the fact we have limited headcount right now. I mean, do we even have the bandwidth to handle that migration?

Ana Petrova: Exactly, I mean, we’ve all seen how that ends up. Or should I say, “how it ends up in delays"?

Daniel Cho: And the last thing we want is to push our timelines out again because we overcommitted. 

Priya Nair: Okay, so can we agree to focus solely on the orders topic for now? That way, we can stabilize before we tackle more complex events?

Wei Lin: Sounds reasonable to me. We can use this time to really optimize our event processing for orders.

Ana Petrova: And who knows? By the time we’re ready for user events, we might have that extra headcount or maybe some magic fairy dust! 

Daniel Cho: *laughs* If only! But yeah, keeping it simple is the way to go for now. 

Priya Nair: So when do we want to revisit the user events migration again?

Wei Lin: How about we give it, say, a couple of months? 

Ana Petrova: Or maybe after we finish the current sprint, we can assess again and see if we feel stronger in numbers?

Daniel Cho: I like that — let’s not let it linger. Just keep it parked until we feel more comfortable.

Priya Nair: Alright then, it’s settled! Orders only for now, user events on the back burner until we’re ready. Thanks, everyone! 

Wei Lin: Awesome, looking forward to it. 

Ana Petrova: Alright, let’s get back to crushing this! 

Daniel Cho: Yeah, let’s do it!