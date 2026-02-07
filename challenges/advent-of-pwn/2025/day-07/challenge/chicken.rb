require 'sinatra'

set :environment, :production
set :bind, '88.77.65.83'
set :port, 80

get '/' do
  "<h1>Go away, you'll never find the flag</h1>"
end

get '/flag' do
  if params['xmas'] == 'hohoho-i-want-the-flag'
    File.read('/flag')
  else
    "<h1>that's not correct</h1>"
  end
end
