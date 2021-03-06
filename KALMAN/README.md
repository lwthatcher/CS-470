<h1>Kalman Lab</h1>

This is a group (pairs) lab.

Use this command for starting our server:

    ./bin/bzrflag --world='maps/empty.bzw' --default-tanks=1 --red-port=50003 --blue-port=50000 --purple-port=50001 --green-port=50002 --default-posnoise=5 --respawn-time=999999999999

Use this command for starting a battle server:

    ./bin/bzrflag --default-tanks=10 --red-port=50003 --blue-port=50000 --purple-port=50001 --green-port=50002 --default-posnoise=5 --respawn-time=999999999999  --friendly-fire --time-limit=240


<h3>objective</h3>
 

The purpose of this lab is to give you an idea of what the Kalman Filter does and under what conditions it works well (HINT: it doesn't work perfectly in every situation). In addition to tracking enemy tanks, the Kalman Filter will help you compensate for sensor noise, which is introduced in this lab. You will be required to do the following:

 

    Code up a few simple "clay pigeon" to aim at (two will meet the assumptions of the Kalman filter, one will not)
    Code up the multivariate Kalman Filter update equations
    Draw the filter's output for your "clay pigeons"
    Compete in a full game with others

Note that the numbers provided below are just a starting point. I expect you to have to adjust them to get this to work, that will be the hard part.
<h2>Description</h2>
<h3>Conforming Clay Pigeon</h3>

The Kalman Filter makes a number of assumptions about the path that the tracked object is following. Your first task is to code several "Clay Pigeon" that conforms to these assumptions. You will make 2 Conforming Clay Pigeons which behave in the following ways:

    "Sitting Duck"-- Just sit there
    Constant x and y velocity (a straight line)

 
<h3>Non-conforming Clay Pigeon (the "Wild Pigeon")</h3>

Your second task is to build a Clay Pigeon that violates the Kalman assumptions in some way (your choice). Try to make it as hard to hit as you can.

 
<h3>The Kalman Agent</h3>

Your Kalman Agent must also plot the density of the output of the Kalman Filter (see GnuplotHelp). You will need to plot your filtered estimate of the current location of the clay pigeons and the projected locations. Please code up the plot early rather than at the end of the project; it is a great debugging tool and will really help you understand what is happening with the Kalman Filter.

Use the empty world (remove all obstacles). Both teams should be run with --[color]-tanks=1 (1 player on each team). Your agent should be run with noise by using --default-posnoise=5 (Please comment on the discussion page or talk/email me if you have trouble with this much noise, try various values). Your agent may rotate but may not move. You should successfully track and reliably (maybe not perfectly) shoot the Conforming Clay Pigeons. There may also be instances where the random starting position of the enemy puts it out of range of your tank for an extended period of time.

Part of your task is to tune your Kalman agent to do as well as possible on your Wild Pigeon. When reporting your results, explaining exactly why you had difficulty and what you tried to do about it. Communicate the creative efforts you used to mislead the Kalman Filter and what you did to try to overcome these problems.

 
<h2>Example Matrices</h2>

To accomplish this lab, it is helpful to understand the "physics" used by the enemy agent. We will represent these physics using matrices as done in the class discussions. You will want to play with the values in these matrices, especially Σx and Σz, and we encourage you to do so in order to better understand how the Kalman Filter works.

Initially, your clay pigeons will be at some unknown position on the playing field, and the velocity and acceleration will both be zero. You can use that information to create your initial estimates of the mean and covariance. The physics are based on the six values in our state vector (in this order, represented as a column vector):

![Alt text](/KALMAN/img/Xt.png?raw=true)

where x and y are the (x,y) position of the enemy agent, \dot{x} is the x component of the agent's velocity, \ddot{x} is the x component of the agent's acceleration, and etc. Note that we use Xt to represent the entire observation at time t.

 
<h3>Initialization</h3>

Given this state vector, the Kalman Filter will produce a mean estimate for this vector μ and a covariance matrix for this vector Σ. So, your initial estimates of the mean and covariance could look like these:

![Alt text](/KALMAN/img/mu_knot.png?raw=true)

which means that you think the agent begins at the origin with no velocity and no acceleration, and

![Alt text](/KALMAN/img/Sigma_knot.png?raw=true)

which means that you are pretty sure that the agent is not accelerating or going anywhere, but that you are pretty unsure exactly where the agent is.

 
<h3>Motion or Transition</h3>

Our model assumes that once every time period (Δt), the enemy agent's state X will be updated by the server as follows:

Xt+1∼N(FXt,Σx)

In other words, the location of the enemy agent is drawn from a normal distribution (represented by "N")  with a mean vector with the value FXt and a variance/covariance of ΣX. You can read the ∼ as "is randomly drawn from". That is, Xt+1 will be randomly chosen from a normal distribution centered at a new location based on the old location (Xt) with the motion model F applied (yielding FXt). Since the initial state and all subsequent states are random variables, these variables are capitalized to be consistent with our notes in class. The F matrix used in this lab is precisely the one that we derived in class using Newton's laws of motion (with one exception):

![Alt text](/KALMAN/img/F.png?raw=true)

where the c indicates that we have a linear friction force working against this agent. If in this lab, you re-compute every half-second then Δt = 0.5. Try setting the friction coefficient c to 0 to start out with because there is no friction in the server. In my experience that works best but some students have said that it was easier to get it running with a small c.

 
<h3>Uncertainty</h3>

Each Xt is a sample drawn from a multivariate normal distribution. In our model the x and y positions and velocities are determined by newtonian physics. The x and y accelerations are uncertain.  A good place to start is with a covariance matrix that allows acceleration to vary from the model more than velocity or position, like the following:

![Alt text](/KALMAN/img/Sigma_x.png?raw=true)

Note that there are some other influences on the behavior of the agent (such as being stopped by running into a wall) that are not included in the newtonian model. For this reason the covariance matrix given above, does not use zeros for the position and velocity entries. You might find that 100 is probably too big for the variance in acceleration. You will want play with the values in this covariance matrix.

The noisy measurements of the enemy position will have zero-mean Gaussian noise with a standard deviation of 5 units in each dimension. The sensor model is as follows:

Zt∼N(HXt,ΣZ)

In this equation, Xt is a random variable representing the true (unknown) state, and Zt is a random variable representing the noisy and limited observations provided by the server. Each observation from the server is a sample from a normal distribution with mean HXt and mean ΣZand is encoded as a 2-dimensional vector. These samples are used to perform inference about Xt.

NOTE: As I recall, while you get x and y positions and \dot{x} and \dot{y} velocities for your own tank, you only get x and y for other tanks.

The observation matrix, H, selects out the two "position" values from the state vector. It looks like this:

![Alt text](/KALMAN/img/H.png?raw=true)

Since these measurements are corrupted by noise, it is important to know the covariance matrix of this noise. Since the standard deviation of the x and y position noise is 5 and since these two noises are uncorrelated, the covariance matrix is given by:

![Alt text](/KALMAN/img/Sigma_z.png?raw=true)

NOTE: I may change this, make it a parameter!

 
<h3>Implementation Hints</h3>

    You are more than welcome to implement your own matrix manipulation code. However, you are encouraged to spend your precious time on more important things. Find a reputable source and download a matrix package. If you are using python, I think all of the needed matrix operators are available in numpy. I think numpy is on the lab machines.
    Here are the three Kalman update equations (NOTE: The third equation is wrong in the first and second edition of the book! It was fixed for the third edition):

Kt + 1 = (FΣtFT + Σx)HT(H(FΣtFT + Σx)HT + Σz) − 1

μt + 1 = Fμt + Kt + 1(zt + 1 − HFμt)

Σt + 1 = (I − Kt + 1H)(FΣtFT + Σx)

    Be careful not to get confused with the different Σ matrices: Σx, Σz and the various Σt matrices (one for each time step t).
    Note that these four matrices are constants, so can be initialized once: F,Σx, H, Σz.
    Note also that since H and F are constant, HT and FT are also constant, and can be precomputed just once.
    Initialize your μ0 and Σ0 matrices at the start of each run.
    Don't be too scared by all the subscripts in the Kalman equations. Just think of t as "the last time" and t + 1 as "this time."
    Note also that the expression (FΣtFT + Σx) occurs three times in the equations, so you may save some time by calculating that first.
    To apply predictions into the future, you don't make additional observations, so you shouldn't use the full equations. Instead, use this equation:

μt + 1 = Fμt
<h2>What to Turn In</h2>

To pass off this lab, you will:

    Submit all of your code electronically.
    Turn in a declaration of time spent by each lab partner
    You must use the Kalman filter and adapt it to this lab problem to get credit for this lab.
    As with the other labs, produce a report that describes what you have done.

Your report should include information about what kinds of transition and covariance matrices you used and how it affected performance. Do meaningful experiments that test the abilities of the filter, and try to make meaningful and insightful observations. Discuss why it works better or worse in various circumstances.

For this assignment, you should write a well-structured report on the work you have done, including the following ingredients:

Time: Please include at the top of page 1 of your report a clear measure (in hours) of how long it took you (each) to complete this project.

[10 points] Design Decisions: The report should specify what you built and what choices you made. Be clear about how you used the output of the Kalman filter in the context of targeting. Please do not simply submit a debug or work log.

[5 points] Quality of your Kalman filter implementation, that is, does it track the target.

[5 points] Quality of your targeting implementation, that is, can it predict the future location of the the target and hit it.

[5 points] Notes and results in building the conforming agent

[10 points] Notes and results in building the non-conforming agent

[5 points] Note and results in hitting the stationary agent using the Kalman filter

[10 points] Notes and results in hitting the conforming agent, that is, can you show that you do better with the Kalman filter than without it.

[10 points] Notes and results in hitting the non-conforming agent

[10 points] Notes and results in hitting a conforming agent built by some other group in the class

[10 points] Notes and results in hitting a non-conforming agent built by some other group in the class
[10 point] Visualization used in the notes and results presented above. Try to tell your story with pictures more than just thousands of words.
 
[20 point] Use the potential fields code and some strategy to build an agent that can compete with another group's agent in a full game of bzrflag (with noise as described here, but WITHOUT the noise from the grid lab)
 
[20 point] Report on your success against other teams.

[10 points] Miscellaneous, including the clarity and structure of your report.

Feedback: Include at the end of your report a short section titled "Feedback". Reflect on your experience in the project and provide any concrete feedback you have for us that would help make this project a better learning experience.

