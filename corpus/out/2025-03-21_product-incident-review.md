---
title: Incident Review
date: 2025-03-21
participants: [Leila Haddad, Omar Siddiqui, Victor Nguyen, Ravi Shah, Grace Kim]
---

Leila Haddad: Alright, thanks everyone for joining on such short notice. Let's dive into the incident from last week. Omar, can you kick us off with what happened?

Omar Siddiqui: Sure, so basically, we had a spike in order failures during the peak hours last Wednesday. I think it was around 5 PM when it all went haywire...

Victor Nguyen: Right, I remember. It was like trying to order a pizza on game night — you just weren’t getting through!

Ravi Shah: *laughs* Exactly! You’d think we’d at least get some pizza out of it.

Grace Kim: I hate to break it to you, but I doubt anyone ordered pizza after dealing with that mess. What do we know about the spike?

Omar Siddiqui: Well, it turned out our database didn’t handle the concurrency properly. I mean, I can’t believe it took us this long to realize we had a bottleneck in the order processing module.

Victor Nguyen: Bottleneck? More like a traffic jam! I could almost hear the screams from our customers.

Ravi Shah: At least they weren’t just hitting refresh over and over. God, that could have been even worse.

Leila Haddad: Let’s focus here — did we figure out if it was just a one-off issue or if there are underlying problems?

Omar Siddiqui: Good question. I suspect it’s a mix of both. But I did notice the load testing wasn’t thorough enough for the new feature we rolled out last month. 

Grace Kim: Really? I thought we’d covered that pretty well! 

Victor Nguyen: Guess it depends on your definition of ‘well.’ I mean, we didn’t expect our customers to go full throttle like it was Black Friday.

Ravi Shah: You know, for the record, I still think we need to re-evaluate our scaling strategies. Shouldn’t we be more prepared for unexpected traffic like that? 

Leila Haddad: Yep, agreed. But we also have to balance that with budget constraints. 

Omar Siddiqui: And also prioritize the feature requests we’ve got lined up. Speaking of, when is the next sprint planning session?

Grace Kim: Next week! I’ll make sure to put this incident on our agenda. 

Victor Nguyen: No pressure, Grace—just don’t forget to bring the muffins like last time!

Ravi Shah: *snickers* Yeah, I promise not to share my “secret recipe” for burnt muffins again!

Leila Haddad: Alright, let’s circle back. Omar, can you provide a summary of the database issues in a document for the sprint?

Omar Siddiqui: Absolutely, I’ll whip something up.

Victor Nguyen: And can we add a section about how not to accidentally start a stampede online?

Grace Kim: Now that’s a feature request I can get behind! 

Ravi Shah: Alright, folks, I think that covers it. Looking forward to those muffins next week!

Leila Haddad: So noted, Ravi! Okay, everyone, thanks for your insights. Let’s tackle this head-on! 

Omar Siddiqui: And maybe tackle lunch afterward? 

Victor Nguyen: Only if there’s pizza this time! 

Grace Kim: That’s a deal! 

Ravi Shah: Count me in for the pizza. Only wide enough not to disrupt our traffic flow, please! 

Leila Haddad: Alright, I’ll see you all next week.