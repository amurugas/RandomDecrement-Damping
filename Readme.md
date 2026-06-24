Summary
If the free-decay response (FDR) of a Single Degree-of-Freedom (SDOF) system is not directly available, it is possible to use ambient vibrations data yo estimate the modal damping ratio. Here, the Random Decrement Technique (RDT) [1], as well as the Natural Excitation Technique (NExT) [2], are used. First, the response of a SDOF to white noise is simulated in the time domain using [3]. Then the IRF is computed using the RDT or NExT. Finally, and an exponential decay is fitted to the envelop of the IRF to obtain the modal damping ratio.

Content
The present submission contains:

a function RDT.,m that implements to Random Decrement Technique (RDT)
a function NExT that implements the Natural Excitation Technique (NExT)
a function expoFit that determine the modal damping ratio by fitting an exponential decay to the envelope of the IRF.
a function CentDiff used to simulate the response to a white noise load of a SDOF in the time domain.
An example file Example.m
Any question, comment or suggestion is welcomed.

References
[1] Ibrahim, S. R. (1977). Random decrement technique for modal identification of structures. Journal of Spacecraft and Rockets, 14(11), 696-700.

[2] James III, O. H., & Came, T. G. (1995). The natural excitation technique (next) for modal parameter extraction from operating structures.

[3] http://www.mathworks.com/matlabcentral/fileexchange/53854-harmonic-excitation-of-a-sdof


## RDT.m 

function [R,t] = RDT(y,ys,T,dt)
%
% [R] = RDT(y,ys,T,dt) returns the free-decay response (R) by
% using the random decrement technique (RDT) to the time serie y, with a
% triggering value ys, and for a duration T
%
% INPUT:
%   y: time series of ambient vibrations: vector of size [1xN]
%   dt : Time step
%   ys: triggering values (ys < max(abs(y)) and here ys~=0)
%   T: Duration of subsegments (T<dt*(numel(y)-1))
% OUTPUT:
%   R: impusle response function
%   t: time vector asociated to R
% 
% Author: E. Cheynet - UiB - last modified 14-05-2020
%%
if T>=dt*(numel(y)-1)
    error('Error: subsegment length is too large');
else
    % number of time step per block
    nT = round(T/dt); % sec
end
if ys==0
    error('Error: ys must be different from zero')
elseif or(ys >=max(y),ys <=min(y)),
    error('Error:  ys must verifiy : min(y) < ys < max(y)')
else
    % find triggering value
    ind=find(diff(y(1:end-nT)>ys)~=0)+1;
    
end
% construction of decay vibration
R = zeros(numel(ind),nT);
for ii=1:numel(ind)
    R(ii,:)=y(ind(ii):ind(ii)+nT-1);
end
% averaging to remove the random part
R = mean(R);
% normalize the R
R = R./R(1);
% time vector corresponding to the R
t = linspace(0,T,numel(R));
end

## NExt.m

function [R,t] = NExT(y,dt,Ts,method)
%
% [R] = NExT(y,ys,T,dt) implements the Natural Excitation Technique to
% retrieve the free-decay response (R) from the cross-correlation
% of the measured output y.
%
% 
% Synthax
% 
%   [R] = NExT(y,dt,Ts,1) calculates R with cross-correlation
%   calculated by using the inverse fast fourier transform of the
%   cross-spectral power densities without zero-padding(method = 1).
%
%   [R] = NExT(y,dt,Ts,2) calculate the R with cross-correlation
%   calculated by using the unbiased cross-covariance function (method = 2)
%
% Input
%   y: time series of ambient vibrations: vector of size [1xN]
%   dt : Time step
%   method: 1 or 2 for the computation of cross-correlation functions
%   T: Duration of subsegments (T<dt*(numel(y)-1))
% 
% Output
% 
% R: impusle response function
% t: time vector asociated to R
% 
% Author: E. Cheynet - UiB - last modified 14-05-2020
%%
if nargin<4, method = 2; end % the fastest method is the default method
if ~ismatrix(y), error('Error: y must be a vector or a matrix'),end
[Nyy,N]=size(y);
if Nyy>N
    y=y';
    [Nyy,N]=size(y);
end
% get the maximal segment length fixed by T
M = round(Ts/dt);
switch method
    case 1
        clear R
        for ii=1:Nyy
            for jj=1:Nyy
                y1 = fft(y(ii,:));
                y2 = fft(y(jj,:));
                h0 = ifft(y1.*conj(y2));
                R(ii,jj,:) = h0(1:M);
            end
        end
        % get time vector t associated to the R
        t = linspace(0,dt.*(size(R,3)-1),size(R,3));
        if Nyy==1
            R = squeeze(R)'; % if Nyy=1
        end
    case 2
        R = zeros(Nyy,Nyy,M+1);
        for ii=1:Nyy
            for jj=1:Nyy
                [dummy,lag]=xcov(y(ii,:),y(jj,:),M,'unbiased');
                R(ii,jj,:) = dummy(end-round(numel(dummy)/2)+1:end);
            end
        end
        if Nyy==1
            R = squeeze(R)'; % if Nyy=1
        end
        % get time vector t associated to the R
        t = dt.*lag(end-round(numel(lag)/2)+1:end);
end
% normalize the R
if Nyy==1
R = R./R(1);
else
end

## function [zeta] = expoFit(y,t,wn,optionPlot)
% [zeta] = expoFit(y,t,wn) returns the damping ratio calcualted by fitting
% an exponential decay to the envelop of the free-decay response.
%
% Input:
%   y: envelop of the free-decay response: vector of size [1 x N]
%   t: time vector [ 1 x N]
%   wn: target eigen frequencies (rad/Hz) :  [1 x 1]
%  optionPlot: 1 to plot the fitted function, and 0 not to plot it.
% 
% Output
%  zeta: modal damping ratio:  [1 x 1]
% 
% author: E. Cheynet  - UiB - last updated: 14-05-2020
% 
%%
% Initialisation
guess = [1,1e-2];
% simple exponentiald ecay function
myFun = @(a,x) a(1).*exp(-a(2).*x);
% application of nlinfit function
coeff = nlinfit(t,y,myFun,guess);
% modal damping ratio:
zeta = abs(coeff(2)./wn);
% alternatively: plot the fitted function
if optionPlot== 1, plot(t,myFun(coeff,t),'r'); end
end

# expoFit.m

function [zeta] = expoFit(y,t,wn,optionPlot)
% [zeta] = expoFit(y,t,wn) returns the damping ratio calcualted by fitting
% an exponential decay to the envelop of the free-decay response.
%
% Input:
%   y: envelop of the free-decay response: vector of size [1 x N]
%   t: time vector [ 1 x N]
%   wn: target eigen frequencies (rad/Hz) :  [1 x 1]
%  optionPlot: 1 to plot the fitted function, and 0 not to plot it.
% 
% Output
%  zeta: modal damping ratio:  [1 x 1]
% 
% author: E. Cheynet  - UiB - last updated: 14-05-2020
% 
%%
% Initialisation
guess = [1,1e-2];
% simple exponentiald ecay function
myFun = @(a,x) a(1).*exp(-a(2).*x);
% application of nlinfit function
coeff = nlinfit(t,y,myFun,guess);
% modal damping ratio:
zeta = abs(coeff(2)./wn);
% alternatively: plot the fitted function
if optionPlot== 1, plot(t,myFun(coeff,t),'r'); end
end

## CentDiff.m

function [y] = CentDiff(F,M,K,C,dt,x0,v0)
% [y] = CentDiff(F,M,K,C,dt,x0,v0)solves numerically the equation of motion
% of a damped system
% 
% 
% INPUT
% F : vector  -- size: [1x N] -- Time series representinf the time history of the load. 
% M : scalar  -- size: [1 x 1] -- Modal mass
% K : scalar  -- size: [1 x 1] -- Modal stifness
% C : scalar  -- size: [1 x 1] -- Modal damping
% dt : scalar  -- size: [1 x 1] -- time step
% x0 : scalar  -- size: [1 x 1] -- initial displacement
% v0 : scalar  -- size: [1 x 1] -- initial velocity
% 
% OUTPUT
% y: time history of the system response to the load
% 
% author: E. Cheynet  - UiB - last updated: 14-05-2020
% 
%%
% Initialisation
N = size(F,2);
% preallocation
y = zeros(size(F));
% initial acceleration
a0 = M\(F(1)-C.*v0-K.*x0);
% initialisation of y (first 2 values).
y0 = x0-dt.*v0+dt^2/2*a0;
y(:,1) = x0;
A = (M./dt.^2+C./(2*dt));
B = ((2*M./dt.^2-K).*y(:,1)+(C./(2*dt)-M./dt.^2).*y0+F(:,1));
y(:,2) = A\B;
% For the rest of integration points
for ii=2:N-1
    A = (M./dt.^2+C./(2*dt));
    B = ((2*M./dt.^2-K).*y(:,ii)+(C./(2*dt)-M./dt.^2).*y(:,ii-1)+F(:,ii)); 
    y(:,ii+1) = A\B;
end
end

### BSD 3-Clause License
 
Copyright (c) 2020, E.  Cheynet
All rights reserved.
 
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
 
1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
 
3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.
 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
